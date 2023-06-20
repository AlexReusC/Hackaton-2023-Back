1. Create virtual environment:

Windows

```
python -m venv ./venv
source venv/Scripts/activate
pip install -r requirements.txt

```

Linux

```
python3 -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run flask app:

```
export FLASK_APP=main
export FLASK_ENV=development
flask --app main --debug run
```
