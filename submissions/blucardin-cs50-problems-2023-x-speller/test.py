import subprocess
import os

print(subprocess.run(["check50", "--local", "cs50/problems/2023/x/speller"],
                      cwd=os.getcwd() + "/submissions" + "/blucardin-cs50-problems-2023-x-speller",
                     capture_output=True))
