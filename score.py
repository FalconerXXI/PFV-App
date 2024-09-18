from hardware import HardwareManager, CPU, GPU
import re

class Score:
    def __init__(self, db_path):
        # Initialize with HardwareManager
        self.hardware_manager = HardwareManager(db_path)

    def match_cpu_score(self, cpu_name):
        # Fetch all CPU scores from the hardware manager
        cpu_scores = self.hardware_manager.get_all_hardware_scores(CPU)
        return cpu_scores.get(cpu_name, "CPU score not found")

    def match_gpu_score(self, gpu_name):
        # Fetch all GPU scores from the hardware manager
        gpu_scores = self.hardware_manager.get_all_hardware_scores(GPU)
        return gpu_scores.get(gpu_name, "GPU score not found")
    
    def normalize_cpu_name(self, cpu_name):
        return re.sub(r'[^a-zA-Z0-9]', '', cpu_name.lower())