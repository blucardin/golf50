import subprocess
import os
import check50

print(subprocess.run(["check50", "--local", "cs50/problems/2023/x/speller"],
                      cwd=os.getcwd() + "/submissionsbin" + "/blucardin-cs50-problems-2023-x-speller",
                     capture_output=True))
