from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os, json, csv, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, "datos")
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DATOS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

TXT_PATH = os.path.join(DATOS_DIR, "datos.txt")
JSON_PATH = os.path.join(DATOS_DIR, "datos.json")
CSV_PATH = os.path.join(DATOS_DIR, "datos.csv")
DB_PATH = os.path.join(DB_DIR, "usuarios.db")

# Ensure files exist
if not os.path.exists(TXT_PATH):
    open(TXT_PATH, "w", encoding="utf-8").close()
if not os.path.exists(JSON_PATH):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nombre", "correo", "timestamp"])

# --- SQLAlchemy setup ---
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False)
    creado_en = Column(DateTime, default=datetime.datetime.utcnow)

    def as_dict(self):
        return {"id": self.id, "nombre": self.nombre, "correo": self.correo, "creado_en": self.creado_en.isoformat()}

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, future=True)

app = Flask(__name__)

# Helpers
def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/formulario")
def formulario():
    return render_template("formulario.html")

@app.route("/procesar", methods=["POST"])
def procesar():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    destino = request.form.get("destino", "txt")
    if destino == "txt":
        _guardar_txt(nombre, correo)
        return redirect(url_for("leer_txt"))
    elif destino == "json":
        _guardar_json(nombre, correo)
        return redirect(url_for("leer_json"))
    elif destino == "csv":
        _guardar_csv(nombre, correo)
        return redirect(url_for("leer_csv"))
    elif destino == "db":
        _guardar_db(nombre, correo)
        return redirect(url_for("leer_db"))
    return redirect(url_for("index"))

# --- TXT ---
def _guardar_txt(nombre="Usuario TXT", correo="usuario.txt@example.com"):
    linea = f"{nombre} | {correo} | {now_iso()}\n"
    with open(TXT_PATH, "a", encoding="utf-8") as f:
        f.write(linea)

@app.route("/guardar_txt")
def guardar_txt():
    nombre = request.args.get("nombre", "Usuario TXT")
    correo = request.args.get("correo", "usuario.txt@example.com")
    _guardar_txt(nombre, correo)
    return render_template("resultado.html", mensaje="Dato guardado en TXT (datos/datos.txt)", datos=None, encabezados=None)

@app.route("/leer_txt")
def leer_txt():
    filas = []
    if os.path.exists(TXT_PATH):
        with open(TXT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                partes = [p.strip() for p in line.split("|")]
                if len(partes) >= 3:
                    filas.append({"nombre": partes[0], "correo": partes[1], "timestamp": partes[2]})
    return render_template("resultado.html", mensaje="Contenido de TXT", datos=filas, encabezados=["nombre","correo","timestamp"])

# --- JSON ---
def _guardar_json(nombre="Usuario JSON", correo="usuario.json@example.com"):
    data = []
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    data.append({"nombre": nombre, "correo": correo, "timestamp": now_iso()})
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/guardar_json")
def guardar_json():
    nombre = request.args.get("nombre", "Usuario JSON")
    correo = request.args.get("correo", "usuario.json@example.com")
    _guardar_json(nombre, correo)
    return render_template("resultado.html", mensaje="Dato guardado en JSON (datos/datos.json)", datos=None, encabezados=None)

@app.route("/leer_json")
def leer_json():
    data = []
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    return render_template("resultado.html", mensaje="Contenido de JSON", datos=data, encabezados=["nombre","correo","timestamp"])

# --- CSV ---
def _guardar_csv(nombre="Usuario CSV", correo="usuario.csv@example.com"):
    with open(CSV_PATH, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([nombre, correo, now_iso()])

@app.route("/guardar_csv")
def guardar_csv():
    nombre = request.args.get("nombre", "Usuario CSV")
    correo = request.args.get("correo", "usuario.csv@example.com")
    _guardar_csv(nombre, correo)
    return render_template("resultado.html", mensaje="Dato guardado en CSV (datos/datos.csv)", datos=None, encabezados=None)

@app.route("/leer_csv")
def leer_csv():
    filas = []
    with open(CSV_PATH, "r", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filas.append(row)
    return render_template("resultado.html", mensaje="Contenido de CSV", datos=filas, encabezados=["nombre","correo","timestamp"])

# --- SQLite (SQLAlchemy) ---
def _guardar_db(nombre="Usuario DB", correo="usuario.db@example.com"):
    session = SessionLocal()
    try:
        u = Usuario(nombre=nombre, correo=correo)
        session.add(u)
        session.commit()
    finally:
        session.close()

@app.route("/guardar_db")
def guardar_db():
    nombre = request.args.get("nombre", "Usuario DB")
    correo = request.args.get("correo", "usuario.db@example.com")
    _guardar_db(nombre, correo)
    return render_template("resultado.html", mensaje="Dato guardado en SQLite (database/usuarios.db)", datos=None, encabezados=None)

@app.route("/leer_db")
def leer_db():
    session = SessionLocal()
    try:
        usuarios = session.query(Usuario).order_by(Usuario.id.desc()).all()
        datos = [u.as_dict() for u in usuarios]
    finally:
        session.close()
    return render_template("resultado.html", mensaje="Contenido de SQLite", datos=datos, encabezados=["id","nombre","correo","creado_en"])

if __name__ == "__main__":
    app.run(debug=True)
