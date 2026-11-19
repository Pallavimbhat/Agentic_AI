@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo Agentic AI Course Organizer - Complete Test Suite
echo ===============================================
echo.
python -m unittest tests.test_agentic_core tests.test_labs_9_14 tests.test_all_14_dynamic tests.test_unified_assistant tests.test_app_integration -v
if errorlevel 1 goto failed
python -m unittest course_organizer.database.test_db_service course_organizer.database.test_extended_db_service course_organizer.agents.test_integrated_lab_agent -v
if errorlevel 1 goto failed
python -m unittest lab3.test_skills lab4.test_memory lab5.test_connectors lab6.test_runtime lab7.test_graph lab8.test_swarm -v
if errorlevel 1 goto failed
echo.
echo ALL TEST GROUPS PASSED.
pause
exit /b 0
:failed
echo.
echo A test group failed. Save the complete output for debugging.
pause
exit /b 1
