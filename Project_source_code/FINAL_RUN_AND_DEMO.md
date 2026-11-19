# Final run and demonstration

1. Extract the project ZIP and open the root folder in VS Code.
2. Create/activate `.venv` and install `requirements.txt`.
3. Run `START_APPLICATION.bat` or `python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002 --reload`.
4. Open `http://127.0.0.1:8002/` and sign in.
5. Use the fourteen `Run Lab 1` … `Run Lab 14` cards to demonstrate each capability, or click `Run complete 14-lab demo`.
6. Expand the execution trace and JSON details after each request.
7. Run `RUN_TESTS.bat` before the demonstration.

The application does not mount a separate `/labs` showcase page. All fourteen guided controls route through the same Academic AI Assistant.
