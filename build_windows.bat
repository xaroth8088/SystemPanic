rmdir /s /q build
rmdir /s /q dist
pyinstaller --onefile --windowed --name=SystemPanic SystemPanic\__main__.py
xcopy /s SystemPanic\GamePaks dist\GamePaks\*
