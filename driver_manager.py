
from selenium_stealth import stealth
import undetected_chromedriver as uc

class DriverManager:
    def __enter__(self):
        options = uc.ChromeOptions()
        options.headless = False
        self.driver = uc.Chrome(use_subprocess=True, options=options)
        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()