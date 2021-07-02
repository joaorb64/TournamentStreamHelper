## HTML-based overlay templates

Here you'll find templates for animated layouts using the program's output.

In `/include/` you'll find `globals.js` which contain general functions used in most template layouts. You'll also find some of the libraries used: `gsap` and `jquery`.

Testing and debugging locally with Chrome:
- Add the flag `--allow-file-access-from-files` when launching Chrome
    - On Windows, you can either `"C:\PathTo\chrome.exe" --allow-file-access-from-files` or open the PowerShell and type `Start-Process "chrome.exe" "--allow-file-access-from-files"`
- Then, you can open a layout `html` file in Chrome, press F12 for developer tools
- Enable *Device toolbar* and set the screen size to 1920x1080
With this, you'll have access to the console logs (and errors) and to quickly edit css rules for easier development