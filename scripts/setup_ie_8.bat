@echo off
rem Stop IE script dialog
rem See https://support.saucelabs.com/hc/en-us/articles/225096267-Resolving-the-Stop-Running-this-Script-dialog-in-Internet-Explorer
reg add "HKCU\Software\Microsoft\Internet Explorer\Styles" /f
reg add "HKCU\Software\Microsoft\Internet Explorer\Styles" /v "MaxScriptStatements" /t REG_DWORD /d 0xFFFFFFFF /f
