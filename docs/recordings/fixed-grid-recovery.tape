Output docs/fixed-grid-recovery.gif

Require python3
Require tesseract

Set Shell "zsh"
Set FontSize 18
Set Width 1200
Set Height 760
Set TypingSpeed 20ms
Set Theme "Catppuccin Mocha"

Hide
Type "rm -rf /tmp/lateletter-fixed-grid-gif-20260812" Enter
Show
Type "./run-sample.sh /tmp/lateletter-fixed-grid-gif-20260812" Enter
Sleep 5s
Type "sed -n '1,22p' /tmp/lateletter-fixed-grid-gif-20260812/machine-ocr.txt" Enter
Sleep 6s
