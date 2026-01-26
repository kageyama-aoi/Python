Running pytest before push...

============================================================== ERRORS ===============================================================
____________________________________________ ERROR collecting 01_勤怠自動化/test_handlers.py _____________________________________________
ImportError while importing test module 'C:\Users\kageyama\Tools\Python\01_勤怠自動化\test_handlers.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
01_勤怠自動化\test_handlers.py:41: in <module>
    from handlers import CrowdLogHandler, TaskReportHandler
E   ModuleNotFoundError: No module named 'handlers'
________________________________________ ERROR collecting 02_スクレイピング（勤怠・TR)/test_handlers.py ________________________________________
ImportError while importing test module 'C:\Users\kageyama\Tools\Python\02_スクレイピング（勤怠・TR)\test_handlers.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
02_スクレイピング（勤怠・TR)\test_handlers.py:41: in <module>
    from handlers import CrowdLogHandler, TaskReportHandler
E   ModuleNotFoundError: No module named 'handlers'
====================================================== short test summary info ====================================================== 
ERROR 01_勤怠自動化/test_handlers.py
ERROR 02_スクレイピング（勤怠・TR)/test_handlers.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
2 errors in 2.05s
Pytest tests failed! Aborting push.
error: failed to push some refs to 'https://github.com/kageyama-aoi/Python.git'
PS C:\Users\kageyama\Tools\Python\07_(掃除)Fileを拡張子ごと振り分け> 
 *  履歴が復元されました 

PS C:\Users\kageyama\Tools\Python\07_(掃除)Fileを拡張子ごと振り分け>  git push origin main
Running pytest before push...

============================================================== ERRORS ===============================================================
____________________________________________ ERROR collecting 01_勤怠自動化/test_handlers.py _____________________________________________
ImportError while importing test module 'C:\Users\kageyama\Tools\Python\01_勤怠自動化\test_handlers.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
01_勤怠自動化\test_handlers.py:41: in <module>
    from handlers import CrowdLogHandler, TaskReportHandler
E   ModuleNotFoundError: No module named 'handlers'
________________________________________ ERROR collecting 02_スクレイピング（勤怠・TR)/test_handlers.py ________________________________________
ImportError while importing test module 'C:\Users\kageyama\Tools\Python\02_スクレイピング（勤怠・TR)\test_handlers.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
02_スクレイピング（勤怠・TR)\test_handlers.py:41: in <module>
    from handlers import CrowdLogHandler, TaskReportHandler
E   ModuleNotFoundError: No module named 'handlers'
====================================================== short test summary info ====================================================== 
ERROR 01_勤怠自動化/test_handlers.py
ERROR 02_スクレイピング（勤怠・TR)/test_handlers.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
2 errors in 0.78s
Pytest tests failed! Aborting push.
error: failed to push some refs to 'https://github.com/kageyama-aoi/Python.git'