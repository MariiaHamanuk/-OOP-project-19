# -OOP-project-19 
Beyond Duty
## About
Beyond Duty is an online platform that helps the military integrate into civilian life through a mentoring system. Our system introduces user to a short questionary to sort the best psychologist based on veteran`s requirements - who will help him take the first steps towards a normal, civilian life. Also user can be part of events organized by volunteers. Very important part about privacy and safety of veterans we are checking on offline interviews each volunteer each  event and only then they are visible for our user.
##Features
1. For all users
- user without autorisation cannot reach any endpoint except for login page and start page
- OAuth if user is registrated because we need an additional info
- ability to exit profile
- ability to edit profile
- different endpoints for different pages
- data is writen in tables (we are using PostgresSQL)
- user stays login
2. For veterans
- can pick events
- can answer some questions to get personalizes list of psuchologists
- can rate psychologists we are using Weighted Influence Aggregation algorythm
3. For psychologist
- they can take a short quiz and be picked by veterans
4. For people who wants to add their events
- verefication
- ability to add events
## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MariiaHamanuk/-OOP-project-19
   cd OOP-project-19
   npm install
   flask install
   npm start
## 5. Technologies Used

## Built With
- HTML, CSS, JavaScript
- Python
- Flask
- PostgresSQL
