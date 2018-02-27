# **Muvik Trending Algorithm**
## **Introduction**
The code is designed to identify which videos are becoming trend among a huge source of videos in ***Muvik*** app. It is written in ***Python 3***, using ***SQLAlchemy*** and ***Flask*** to connect to ***MySQL*** database.

## **Requirements**
At the local repository run the command line to install the requirements:

```sudo pip3 install -r requirements.txt```

## **Run the code**

The code uses **MySQL** database through ***MariaDB***. To run the code, use the command:

```python3 crud.py```

## **Run with gunicorn for run multithreading**

Install : ``` sudo pip3 install gunicorn```. 
Create file ```wsgi.py``` into project with content:

```
from crud import app

if __name__ == "__main__":
    app.run()
```

run with 3 thread : 

```
gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app
```

## **Instructions**

### **To POST new video or update new information of a video**
Go to ```localhost:5000/video```, use **POST** method and send the data in one line in the form of: 

```
[   
    {"videoid":"2777033_9112_ios_4869_12764182","video_timestamp":"1511802250603","view_timestamp":["1511803040099", "1511804248440"]},
    {"videoid":"2777033_9112_ios_4869_12764182","video_timestamp":"1511802250603","view_timestamp":["1511803040099", "1511804248440"]},
    {"videoid":"2777033_9112_ios_4869_12764182","video_timestamp":"1511802250603","view_timestamp":["1511803040099", "1511804248440"]}
]
```
### **To view the list of videos**
Go to ```localhost:5000/video``` and use **GET** method
### **To view the list of videos with view timestamp**
Go to ```localhost:5000/viewtime``` and use **GET** method
### **To get trending list**
Go to ```localhost:5000/trending``` and use **GET** method

### **To compute new kl_score of each video and delete old videos**
Run: ```python3 get.py``` 

Compute ***kl_score*** function and ***delete old videos*** function are seperated into a new **Python** file to reduce the amount of time when starting a new session from server. 