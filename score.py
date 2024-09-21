from hardware import HardwareManager, CPU, GPU
import re

class Score:
    def __init__(self, cpu_name, gpu_name, form_factor, ram, storage):
        # Initialize with HardwareManager
        self.cpu_name = cpu_name
        self.gpu_name = gpu_name
        self.form_factor = form_factor
        self.storage = storage
        self.ram = ram

    def cpu_score(self, cpu_name):
        # Fetch all CPU scores from the hardware manager
        cpu_scores = self.hardware_manager.get_all_hardware_scores(CPU)
        return cpu_scores.get(cpu_name, "CPU score not found")

    def gpu_score(self, gpu_name):
        # Fetch all GPU scores from the hardware manager
        gpu_scores = self.hardware_manager.get_all_hardware_scores(GPU)
        return gpu_scores.get(gpu_name, "GPU score not found")

    def ff_score(self, form_factor):
        # Fetch all form factor scores from the hardware manager
        ff_scores = self.hardware_manager.get_all_hardware_scores(CPU)
        return ff_scores.get(form_factor, "Form factor score not found")