from flask import Flask, render_template, abort, jsonify, send_from_directory, request,redirect, url_for
import os
import sys
sys.path.insert(0, "/var/www/html/students_26/Team15/flask_app/vendor")
import mysql.connector
import hashlib
import tempfile
import json
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__, template_folder="templates", static_folder="static")
ISSUE_SUBMISSIONS_DIR = os.path.join(app.root_path, "submitted_issues")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

APP_BASE = "/students_26/Team15/flask_app/app"

def make_app_url(endpoint, **values):
    return APP_BASE + url_for(endpoint, **values)

def get_temp_plots_dir():
    # Use a fixed shared directory in /tmp that all Apache processes can access
    plots_dir = "/tmp/tpsd_plots_shared"
    os.makedirs(plots_dir, exist_ok=True)
    return plots_dir

def get_db_connection():
    return mysql.connector.connect(
        host="bioed-new.bu.edu",
        port=4253,
        user="lltsdxyz",
        password="lltsdxyz",
        database="Team15"
    )

@app.route("/")
def home():

    stats = {
        "compound_count": None,
        "absorption_count": None,
        "emission_count": None,
        "class_count": 1
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS count FROM compound")
        stats["compound_count"] = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM absorption_spectrum")
        stats["absorption_count"] = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM fluorescence_spectrum")
        stats["emission_count"] = cursor.fetchone()["count"]

        cursor.close()
        conn.close()
    except Exception as error:
        print("DEBUG home stats unavailable:", error)
    return render_template("index.html", stats=stats)


@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/report_issue", methods=["POST"])
def report_issue():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()
    submitted_at = datetime.now(timezone.utc).isoformat()

    issue = {
        "submitted_at": submitted_at,
        "name": name,
        "email": email,
        "message": message,
    }

    os.makedirs(ISSUE_SUBMISSIONS_DIR, exist_ok=True)

    filename_timestamp = submitted_at.replace(":", "-").replace("+", "_")
    issue_hash = hashlib.sha256(
        f"{submitted_at}|{email}|{message}".encode("utf-8")
    ).hexdigest()[:10]

    issue_path = os.path.join(
        ISSUE_SUBMISSIONS_DIR,
        f"issue_{filename_timestamp}_{issue_hash}.json"
    )

    with open(issue_path, "w", encoding="utf-8") as issue_file:
        json.dump(issue, issue_file, indent=2)

    return render_template(
        "issue_submitted.html",
        name=name,
        email=email,
        message=message
    )

@app.route("/search")
def search_page():
    return render_template("search+results.html")

@app.route("/api/search")
def api_search():
    compound_name = request.args.get("compound_name", "").strip()
    solvent = request.args.get("solvent", "").strip()
    abs_min = request.args.get("abs_min", "").strip()
    abs_max = request.args.get("abs_max", "").strip()
    em_min = request.args.get("em_min", "").strip()
    em_max = request.args.get("em_max", "").strip()

    query = """
    SELECT DISTINCT
        c.compound_id,
        c.compound_name,
        COALESCE(f.solvent, a.solvent) AS solvent,
        a.absorption_lambda_max_nm,
        f.emission_lambda_max_nm,
        f.quantum_yield
    FROM compound c
    LEFT JOIN fluorescence_spectrum f
        ON c.compound_id = f.compound_id
    LEFT JOIN absorption_spectrum a
        ON c.compound_id = a.compound_id
    WHERE 1=1
    """

    params = []

    if compound_name:
        query += " AND c.compound_name LIKE %s"
        params.append("%" + compound_name + "%")

    if solvent:
        query += " AND (f.solvent LIKE %s OR a.solvent LIKE %s)"
        params.extend(["%" + solvent + "%", "%" + solvent + "%"])

    if abs_min:
        query += " AND a.absorption_lambda_max_nm >= %s"
        params.append(float(abs_min))

    if abs_max:
        query += " AND a.absorption_lambda_max_nm <= %s"
        params.append(float(abs_max))

    if em_min:
        query += " AND f.emission_lambda_max_nm >= %s"
        params.append(float(em_min))

    if em_max:
        query += " AND f.emission_lambda_max_nm <= %s"
        params.append(float(em_max))

    query += """
    ORDER BY c.compound_id
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(results)

    except Exception as error:
        print("DEBUG api_search error:", error)
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


@app.route("/compound/<int:compound_id>")
def compound_detail(compound_id):
    print(f"DEBUG - app.root_path: {app.root_path}")
    print(f"DEBUG - Current working directory: {os.getcwd()}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT c.compound_id,
           c.compound_name,
           c.lab_code,
           c.structure_file,
           c.notes,
           COALESCE(f.solvent, a.solvent) AS solvent,
           f.emission_lambda_max_nm,
           f.quantum_yield,
           f.measurement_instrument,
           f.measurement_year,
           f.reference_code,
           f.investigator,
           f.ems_file_name,
       f.ems_file_path,
       a.absorption_lambda_max_nm,
           a.file_name AS abs_file_name,
       a.file_path AS abs_file_path
    FROM compound c
    LEFT JOIN fluorescence_spectrum f
      ON c.compound_id = f.compound_id
    LEFT JOIN absorption_spectrum a
      ON c.compound_id = a.compound_id
    WHERE c.compound_id = %s
    """

    cursor.execute(query, (compound_id,))
    compound = cursor.fetchone()

    cursor.close()
    conn.close()

    if not compound:
        abort(404)

    detail_plots = {
        "fluorescence": generate_detail_plot(compound, "fluorescence"),
        "absorption": generate_detail_plot(compound, "absorption")
    }

    return render_template("compound_detail.html", compound=compound, detail_plots=detail_plots)

# route for plot generating
def read_spectrum_file(file_path):
    wavelengths = []
    intensities = []

    with open(file_path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.replace(",", " ").split()

            if len(parts) >= 2:
                try:
                    wavelengths.append(float(parts[0]))
                    intensities.append(float(parts[1]))
                except ValueError:
                    continue

    return wavelengths, intensities

def generate_detail_plot(compound, spectrum_type):
	file_name = compound.get("ems_file_name") if spectrum_type == "fluorescence" else compound.get("abs_file_name")

	# DEBUG
	print(f"DEBUG generate_detail_plot - spectrum_type: {spectrum_type}")
	print(f"DEBUG generate_detail_plot - file_name: {file_name}")

	if not file_name:
		print(f"DEBUG generate_detail_plot - No file_name, returning None")
		return None

	file_path = spectrum_file_path(spectrum_type, file_name)
	print(f"DEBUG generate_detail_plot - file_path: {file_path}")
	print(f"DEBUG generate_detail_plot - file exists: {os.path.exists(file_path)}")

	if not os.path.exists(file_path):
		print(f"DEBUG generate_detail_plot - File does not exist, returning None")
		# Try to list what's actually IN the emission directory
		try:
			emission_dir = os.path.join(app.static_folder, "uploaded_data", "emission")
			print(f"DEBUG - Trying to list: {emission_dir}")
			files = os.listdir(emission_dir)
			print(f"DEBUG - Files in emission dir (first 10): {files[:10]}")
		except Exception as e:
			print(f"DEBUG - Error listing emission directory: {e}")
		return None

	wavelengths, values = read_spectrum_file(file_path)
	print(f"DEBUG generate_detail_plot - wavelengths count: {len(wavelengths)}")

	if not wavelengths:
		print(f"DEBUG generate_detail_plot - No wavelengths, returning None")
		return None

	file_hash = hashlib.md5(file_name.encode("utf-8")).hexdigest()[:10]
	plot_filename = f"compound_{compound['compound_id']}_{spectrum_type}_{file_hash}.png"
	plot_path = os.path.join(get_temp_plots_dir(), plot_filename)

	print(f"DEBUG generate_detail_plot - plot_path: {plot_path}")

	if spectrum_type == "fluorescence":
		title = f"Emission Spectrum - {compound['compound_name']}"
		y_label = "Intensity"
	else:
		title = f"Absorption Spectrum - {compound['compound_name']}"
		y_label = "Absorbance"

	plt.figure(figsize=(10, 6))
	plt.plot(wavelengths, values, linewidth=2)
	plt.xlabel("Wavelength (nm)")
	plt.ylabel(y_label)
	plt.title(title)
	plt.grid(True, alpha=0.3)
	plt.tight_layout()
	plt.savefig(plot_path, dpi=150, bbox_inches="tight")
	plt.close()

	# DEBUG: Verify the file was created
	print(f"DEBUG - Plot file created: {os.path.exists(plot_path)}")
	if os.path.exists(plot_path):
		print(f"DEBUG - Plot file size: {os.path.getsize(plot_path)} bytes")

	final_url = f"/students_26/Team15/flask_app/app/tmp_plots/{plot_filename}"
	print(f"DEBUG generate_detail_plot - final URL: {final_url}")
	return final_url

@app.route("/tmp_plots/<path:filename>")
def temporary_plot(filename):
    temp_dir = get_temp_plots_dir()
    print(f"DEBUG temporary_plot - Looking for: {filename}")
    print(f"DEBUG temporary_plot - In directory: {temp_dir}")
    print(f"DEBUG temporary_plot - File exists: {os.path.exists(os.path.join(temp_dir, filename))}")
    return send_from_directory(temp_dir, filename)

@app.route("/api/spectrum/<int:compound_id>/<spectrum_type>")
def get_spectrum_data(compound_id, spectrum_type):
    file_name = request.args.get("file")

    if spectrum_type not in {"absorption", "fluorescence"}:
        return jsonify({"success": False, "error": "Invalid spectrum type"}), 400

    if not file_name:
        return jsonify({"success": False, "error": "No file specified"}), 400

    file_path = spectrum_file_path(spectrum_type, file_name)

    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "File not found"}), 404

    wavelengths, values = read_spectrum_file(file_path)

    if not wavelengths:
        return jsonify({"success": False, "error": "No data in file"}), 400

    return jsonify({
        "success": True,
        "compound_id": compound_id,
        "spectrum_type": spectrum_type,
        "points": [
            {"x": wavelength, "y": value}
            for wavelength, value in zip(wavelengths, values)
        ]
    })

@app.route("/api/plot/<int:compound_id>/fluorescence")
def generate_fluorescence_plot(compound_id):
    file_name = request.args.get("file")

    if not file_name:
        return jsonify({"success": False, "error": "No file specified"}), 400

    file_path = os.path.join(
        app.root_path,
        "static",
        "uploaded_data",
        "emission",
        file_name
    )

    print("DEBUG fluorescence file_path:", file_path)
    print("DEBUG fluorescence exists:", os.path.exists(file_path))

    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "File not found"}), 404

    wavelengths, intensities = read_spectrum_file(file_path)

    if not wavelengths:
        return jsonify({"success": False, "error": "No data in file"}), 400

    plots_dir = os.path.join(app.root_path, "static", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    plot_filename = f"compound_{compound_id}_fluorescence.png"
    plot_path = os.path.join(plots_dir, plot_filename)

    plt.figure(figsize=(10, 6))
    plt.plot(wavelengths, intensities, linewidth=2)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Intensity")
    plt.title(f"Fluorescence Spectrum - Compound {compound_id}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()

    plot_url = make_app_url("static", filename=f"plots/{plot_filename}")

    return jsonify({
        "success": True,
        "plot_url": plot_url
    })

@app.route("/api/plot/<int:compound_id>/absorption")
def generate_absorption_plot(compound_id):
    file_name = request.args.get("file")

    if not file_name:
        return jsonify({"success": False, "error": "No file specified"}), 400

    file_path = os.path.join(
        app.root_path,
        "static",
        "uploaded_data",
        "absorption",
        file_name
    )

    print("DEBUG absorption file_path:", file_path)
    print("DEBUG exists:", os.path.exists(file_path))

    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "File not found"}), 404

    wavelengths, absorbance = read_spectrum_file(file_path)

    if not wavelengths:
        return jsonify({"success": False, "error": "No data in file"}), 400

    plots_dir = os.path.join(app.root_path, "static", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    plot_filename = f"compound_{compound_id}_absorption.png"
    plot_path = os.path.join(plots_dir, plot_filename)

    plt.figure(figsize=(10, 6))
    plt.plot(wavelengths, absorbance, linewidth=2)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Absorbance")
    plt.title(f"Absorption Spectrum - Compound {compound_id}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()

    plot_url = make_app_url("static", filename=f"plots/{plot_filename}")

    return jsonify({
        "success": True,
        "plot_url": plot_url
    })

# route for downloading raw data files
@app.route("/download/<file_type>/<path:filename>")
def download_file(file_type, filename):
    from flask import send_from_directory

    if file_type == 'emission':
        directory = os.path.join('static', 'uploaded_data', 'emission')
    elif file_type == 'absorption':
        directory = os.path.join('static', 'uploaded_data', 'absorption')
    else:
        abort(404)

    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

def spectrum_file_path(file_type, file_name):
    folder = "emission" if file_type == "fluorescence" else "absorption"
    return os.path.join(
        "/var/www/html/students_26/Team15/flask_app",
	"static",
        "uploaded_data",
        folder,
        os.path.basename(file_name)
    )

def get_float_arg(name, default=None, minimum=None, maximum=None):
    value = request.args.get(name, "").strip()

    if not value:
        return default

    try:
        number = float(value)
    except ValueError:
        return default

    if minimum is not None:
        number = max(number, minimum)

    if maximum is not None:
        number = min(number, maximum)

    return number



def build_compare_plot(compounds, file_type, plot_options):
    plot_rows = []
    x_min = plot_options["x_min"]
    x_max = plot_options["x_max"]

    for compound in compounds:
        file_name = compound.get("ems_file_name") if file_type == "fluorescence" else compound.get("abs_file_name")

        if not file_name:
            continue

        file_path = spectrum_file_path(file_type, file_name)

        if not os.path.exists(file_path):
            continue

        wavelengths, values = read_spectrum_file(file_path)

        if not wavelengths or not values:
            continue

        filtered_points = [
            (wavelength, value)
            for wavelength, value in zip(wavelengths, values)
            if (x_min is None or wavelength >= x_min) and (x_max is None or wavelength <= x_max)
        ]

        if not filtered_points:
            continue

        wavelengths = [point[0] for point in filtered_points]
        values = [point[1] for point in filtered_points]

        max_value = max(abs(value) for value in values)
        if plot_options["normalize"] and max_value:
            values = [value / max_value for value in values]

        plot_rows.append({
            "compound_id": compound["compound_id"],
            "compound_name": compound["compound_name"],
            "wavelengths": wavelengths,
            "values": values
        })

    if not plot_rows:
        return None

    plots_dir = os.path.join(app.root_path, "static", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    compound_ids = "_".join(str(compound["compound_id"]) for compound in compounds)
    option_hash = hashlib.md5(str(sorted(plot_options.items())).encode("utf-8")).hexdigest()[:8]
    filename_hash = hashlib.md5(f"{file_type}:{compound_ids}:{option_hash}".encode("utf-8")).hexdigest()[:10]
    plot_filename = f"compare_{file_type}_{filename_hash}.png"
    plot_path = os.path.join(plots_dir, plot_filename)

    title = "Fluorescence Spectra Comparison" if file_type == "fluorescence" else "Absorption Spectra Comparison"

    plt.figure(figsize=(11, 6))
    for row in plot_rows:
        label = f"{row['compound_id']} - {row['compound_name']}"
        plt.plot(row["wavelengths"], row["values"], linewidth=plot_options["line_width"], label=label)

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Normalized signal" if plot_options["normalize"] else "Signal")
    plt.title(title)
    if plot_options["show_grid"]:
        plt.grid(True, alpha=0.3)
    else:
        plt.grid(False)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {
        "plot_url": make_app_url("static", filename=f"plots/{plot_filename}"),
        "compound_ids": [row["compound_id"] for row in plot_rows]
    }


def build_compare_chart_data(compounds, file_type):
    series = []

    for compound in compounds:
        file_name = compound.get("ems_file_name") if file_type == "fluorescence" else compound.get("abs_file_name")

        if not file_name:
            continue

        file_path = spectrum_file_path(file_type, file_name)

        if not os.path.exists(file_path):
            continue

        wavelengths, values = read_spectrum_file(file_path)

        if not wavelengths or not values:
            continue

        series.append({
            "compound_id": compound["compound_id"],
            "compound_name": compound["compound_name"],
            "label": f"{compound['compound_id']} - {compound['compound_name']}",
            "data": [
                {"x": wavelength, "y": value}
                for wavelength, value in zip(wavelengths, values)
            ]
        })

    return series


@app.route("/compare")
def compare():
    id_text = request.args.get("ids", "")
    spectra_values = request.args.getlist("spectra")
    if spectra_values:
        spectra_text = ",".join(spectra_values)
    else:
        spectra_text = "absorption,fluorescence"

    plot_options = {
        "normalize": request.args.get("normalize", "1") == "1",
        "show_grid": request.args.get("grid", "1") == "1",
        "line_width": get_float_arg("line_width", default=2.0, minimum=0.5, maximum=6.0),
        "x_min": get_float_arg("x_min"),
        "x_max": get_float_arg("x_max")
    }

    if (
        plot_options["x_min"] is not None
        and plot_options["x_max"] is not None
        and plot_options["x_min"] > plot_options["x_max"]
    ):
        plot_options["x_min"], plot_options["x_max"] = plot_options["x_max"], plot_options["x_min"]

    requested_spectra = {
        spectrum.strip()
        for spectrum in spectra_text.split(",")
        if spectrum.strip() in {"absorption", "fluorescence"}
    }

    if not requested_spectra:
        requested_spectra = {"absorption", "fluorescence"}

    compound_ids = []

    for value in id_text.split(","):
        value = value.strip()
        if value.isdigit():
            compound_id = int(value)
            if compound_id not in compound_ids:
                compound_ids.append(compound_id)

    show_absorption = "absorption" in requested_spectra
    show_fluorescence = "fluorescence" in requested_spectra

    if not compound_ids:
        return render_template(
            "compare.html",
            compounds=[],
            absorption_plot=None,
            fluorescence_plot=None,
            chart_data={"absorption": [], "fluorescence": []},
            show_absorption=show_absorption,
            show_fluorescence=show_fluorescence,
            plot_options=plot_options,
            selected_ids=id_text
        )

    placeholders = ",".join(["%s"] * len(compound_ids))
    query = f"""
    SELECT c.compound_id,
           c.compound_name,
           c.lab_code,
           c.structure_file,
           f.solvent AS fluorescence_solvent,
           f.emission_lambda_max_nm,
           f.quantum_yield,
           f.ems_file_name,
           a.solvent AS absorption_solvent,
           a.absorption_lambda_max_nm,
           a.file_name AS abs_file_name
    FROM compound c
    LEFT JOIN fluorescence_spectrum f
      ON c.compound_id = f.compound_id
    LEFT JOIN absorption_spectrum a
      ON c.compound_id = a.compound_id
    WHERE c.compound_id IN ({placeholders})
    ORDER BY c.compound_id
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, compound_ids)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    compounds_by_id = {}
    for row in rows:
        compound_id = row["compound_id"]

        if compound_id not in compounds_by_id:
            compounds_by_id[compound_id] = {
                "compound_id": compound_id,
                "compound_name": row["compound_name"],
                "lab_code": row["lab_code"],
                "structure_file": row["structure_file"],
                "fluorescence_solvent": row["fluorescence_solvent"],
                "emission_lambda_max_nm": row["emission_lambda_max_nm"],
                "quantum_yield": row["quantum_yield"],
                "ems_file_name": row["ems_file_name"],
                "absorption_solvent": row["absorption_solvent"],
                "absorption_lambda_max_nm": row["absorption_lambda_max_nm"],
                "abs_file_name": row["abs_file_name"]
            }
            continue

        compound = compounds_by_id[compound_id]
        if not compound["ems_file_name"] and row["ems_file_name"]:
            compound["fluorescence_solvent"] = row["fluorescence_solvent"]
            compound["emission_lambda_max_nm"] = row["emission_lambda_max_nm"]
            compound["quantum_yield"] = row["quantum_yield"]
            compound["ems_file_name"] = row["ems_file_name"]

        if not compound["abs_file_name"] and row["abs_file_name"]:
            compound["absorption_solvent"] = row["absorption_solvent"]
            compound["absorption_lambda_max_nm"] = row["absorption_lambda_max_nm"]
            compound["abs_file_name"] = row["abs_file_name"]

    compounds = [compounds_by_id[compound_id] for compound_id in compound_ids if compound_id in compounds_by_id]
    chart_data = {
        "absorption": build_compare_chart_data(compounds, "absorption") if show_absorption else [],
        "fluorescence": build_compare_chart_data(compounds, "fluorescence") if show_fluorescence else []
    }
    return render_template(
        "compare.html",
        compounds=compounds,
        absorption_plot=None,
        fluorescence_plot=None,
        chart_data=chart_data,
        show_absorption=show_absorption,
        show_fluorescence=show_fluorescence,
        plot_options=plot_options,
        selected_ids=",".join(str(compound_id) for compound_id in compound_ids)
    )

if __name__ == "__main__":
    app.run(debug=True)
