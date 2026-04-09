**Energy Level Tracker**
A personal optimization web app designed to help you track your daily habits and predict your peak focus hours.
Instead of guessing when you will feel your best, this tool uses your own historical data (sleep, nutrition, stress, and exact caffeine intake) to build a personalized predictive model. 

**Key Features**

  * Holistic Logging: Track exact sleep times, sleep quality, meal quality, stress levels, and exercise.
  * Pharmacokinetic Caffeine Tracking: Log multiple coffees by their exact time and milligrams. The app calculates the cumulative, real-time exponential decay of caffeine in your system.
  * Predictive Modeling: Runs an Ordinary Least Squares regression using statsmodels to pinpoint exactly which variables drive or drain your energy.
  * Optimal Schedule Generation: Plan your sleep and morning coffee, and the app will generate a visual hour-by-hour forecast of your energy for the day using your personalized model.

**Tech Stack**

  * Python 3.11
  * Streamlit for the interactive web interface
  * Pandas and NumPy for data manipulation and mathematical modeling
  * Statsmodels for the OLS regression analysis
  * Plotly for rendering interactive, clean data visualizations

**How to Run Locally**

1.  Clone the repository by typing git clone [https://github.com/yourusername/energy-level-tracker.git](https://www.google.com/search?q=https://github.com/yourusername/energy-level-tracker.git) in your terminal, then type cd energy-level-tracker to enter the folder.
2.  Set up a virtual environment to keep dependencies clean by running python -m venv .venv, and then activate it using source .venv/bin/activate on Mac or .venv\\Scripts\\activate on Windows.
3.  Install dependencies by running pip install streamlit pandas statsmodels numpy plotly.
4.  Run the app by launching the Streamlit server using the command python -m streamlit run app.py. The app will automatically open in your default web browser.

**How to Use**

1.  Log Entry Tab: Make it a habit to log your current state a few times a day. Enter your exact time, energy level, sleep data, and list your coffees (for example, 08:00=100, 13:00=50).
2.  Data and Model Tab: Once you have at least 5 entries, click Run Optimization Model. The app will calculate your variance explained so you can see how accurate your model is becoming.
3.  Optimal Schedule Tab: Plug in your planned sleep and coffee schedule for tomorrow to see exactly when you should schedule your deep, focused work versus light admin tasks.
