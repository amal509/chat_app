# Chat App



# Requirements

- Python 3.10+
- pip


# Setup

# 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

# 2. Install dependencies

```bash
pip install -r requirements.txt
```

# 3. Set up environment variables

Go into the `chat_app` folder and create a `.env` file:

```bash
cd chat_app
```

Create `.env` with the following content:

```
SECRET_KEY=secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=UTC
```

To generate a secret key, run:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it as the value for `SECRET_KEY`.

# 4. Run migrations

```bash
python manage.py migrate
```

# 5. Start the server

```bash
python manage.py runserver
```

Open your browser and go to `http://127.0.0.1:8000`