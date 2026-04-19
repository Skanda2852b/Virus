
Below is the corrected **simple step‑by‑step setup** that works with your YOLO‑based implementation. No extra model downloads are needed (YOLO weights are usually downloaded automatically by your code or are already included).

---

## **Simple Setup & Run (for YOLO version)**

### 1. **Open a terminal / PowerShell**  
   Navigate to the project folder (e.g., `D:\Projects\Virus`).

### 2. **Create a virtual environment (optional but recommended)**  
   ```bash
   python -m venv venv
   ```
   Activate:
   - **Windows PowerShell:** `.\venv\Scripts\Activate`
   - **Linux/macOS:** `source venv/bin/activate`

### 3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   (Make sure your `requirements.txt` includes `ultralytics` or `yolov5` if you use YOLO.)

### 4. **Run the application**  
   ```bash
   python app.py
   ```

### 5. **Open your browser** and go to:  
   ```
   http://127.0.0.1:5000
   ```

### 6. **Login as admin**  
   - Username: `admin`  
   - Password: `admin123`

### 7. **Use the system**  
   - Add teachers → add students → capture face images → train model → start attendance → monitor behaviour.

---

## **Important Notes for YOLO**

- No need to download MobileNet SSD files – your YOLO code will handle its own weights (usually downloaded on first run or placed in a `weights/` folder).
- If you encounter missing YOLO weights, ensure your code downloads them automatically or place the `.pt` file manually as required.

---

That’s it. The system will start and you can log in immediately.
