import json
import time
from threading import Thread
from collections import deque
import numpy as np
from einops import rearrange
import onnxruntime as rt


class SLInference:
    def __init__(self, config_path):
        self.running = True
        self.config = self.read_config(config_path)
        self.model = self.load_model()
        self.input_queue = deque(maxlen=self.config['window_size']*2)
        self.pred = ""
        self.labels = self.load_labels()
        
    def read_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_model(self):
        return rt.InferenceSession(
            self.config['path_to_model'],
            providers=[self.config['provider']]
        )
    
    def load_labels(self):
        with open(self.config['path_to_class_list'], 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in (line.strip().split('\t') for line in f)}
    
    def predict(self):
        if len(self.input_queue) < self.config['window_size']:
            return
        
        frames = list(self.input_queue)[-self.config['window_size']:]
        input_data = np.array(frames).astype(np.float32) / 255.0
        input_data = rearrange(input_data, "t h w c -> 1 c t h w")
        
        outputs = self.model.run(
            [self.model.get_outputs()[0].name],
            {self.model.get_inputs()[0].name: input_data}
        )
        
        probs = np.squeeze(outputs[0])
        pred_idx = np.argmax(probs)
        
        if probs[pred_idx] > self.config['threshold']:
            self.pred = self.labels.get(pred_idx, 'unknown')
        else:
            self.pred = ''

    def worker(self):
        while self.running:
            self.predict()
            time.sleep(0.1)
    
    def start(self):
        Thread(target=self.worker, daemon=True).start() 