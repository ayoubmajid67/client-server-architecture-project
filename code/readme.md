Here's a **complete documentation** to set up your distributed Flask task calculator project using Python `venv`. This guide will walk you through installing dependencies, setting up virtual environments, running the master and slave services, and testing the system.

---

## 📁 Project Structure

```
distributed_calculator/
├── master.py
├── slave.py
├── utils.py
├── requirements.txt
└── README.md
```

---

## 📋 Prerequisites

* Python 3.8+
* pip
* Internet connection to install packages

---

## 🔧 1. Create and Activate Virtual Environment

**Linux/MacOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (CMD):**

```cmd
python -m venv venv
venv\Scripts\activate
```

---

## 📦 2. Install Dependencies

Create a `requirements.txt`:

```txt
flask
requests
```

Then install:

```bash
pip install -r requirements.txt
```

---

## 🧠 3. Start the Master Server

1. Open a terminal.
2. Activate the virtual environment (if not already).
3. Run:

```bash
python master.py
```

This starts the master on `http://localhost:5000`.

---

## 🤖 4. Start Slave Servers

Each slave must run on a different port. Use terminal tabs or new windows.

**Example to start Slave 1 (port 6000):**

```bash
python slave.py slave-1
```

**Example to start Slave 2 (port 6001):**

1. Change `WEBHOOK_PORT` to 6001 in `slave.py` or pass dynamically.
2. Duplicate and adjust slave file if needed.

> The slave automatically registers itself with the master using `http://<master-ip>:5000`.

---

## 🧪 5. Submit a Task

Use **Postman** or `curl`:

```bash
curl -X POST http://localhost:5000/submit-task \
  -H "Content-Type: application/json" \
  -d '{"payload": "4 * (2 + 3)"}'
```

---

## ✅ 6. Monitor

* View task statuses:
  [http://localhost:5000/tasks](http://localhost:5000/tasks)

* View registered slaves:
  [http://localhost:5000/slaves](http://localhost:5000/slaves)

* Check slave status manually:
  [http://localhost:6000/status/slave-1](http://localhost:6000/status/slave-1)

---

## 🧹 7. Deactivate Environment

When done:

```bash
deactivate
```

---

## 🛠 Optional: Run Multiple Slaves with Custom Ports

You can duplicate `slave.py` or add a CLI parameter to dynamically adjust the port and slave ID. Here's an improvement:

### Example:

```bash
python slave.py slave-2 6001
```

And update this in `slave.py`:

```python
SLAVE_ID = sys.argv[1]
WEBHOOK_PORT = int(sys.argv[2])
```

---

Let me know if you want me to generate the `README.md` with this content or include Docker support.
