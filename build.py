import PyInstaller.__main__ as pi
import sys


exec_name = "dts"

params = [
  "src/main.py",
  "--onedir",
  "--clean",
  "--console",
  f"--name={exec_name}",
  "--icon=assets/icon.ico",
  # ttkbootstrap loads its themes from JSON data files
  "--collect-all=ttkbootstrap",
]

def build():
  pi.run(params)
  pass



if __name__ == "__main__":
  build()
