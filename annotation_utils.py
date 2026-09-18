from IPython.display import display, clear_output
import ipywidgets as widgets
import gspread

LEVEL1_LABELS  = ["Explicit Help-Seeking", "Implicit Help-Seeking", "Not Help-Seeking", "Unsure"]
LEVEL2_LABELS  = ["Informational Support-Seeking", "Emotional Support-Seeking", "Esteem Support-Seeking", "Network Support-Seeking", "None"]
LEVEL2_TRIGGER = ["Explicit Help-Seeking", "Implicit Help-Seeking"]

WORKSHEET_NAME  = "posts"
ANNOTATION_COL  = 3
ANNOTATION_COL2 = 4

ANNOTATOR_SHEETS = {
    "adhamcr80@gmail.com":   "https://docs.google.com/spreadsheets/d/1yCjM2mD4tdPhAvdMHYEj6J05OsZQ2B07qRwo2yfavUk/edit?gid=1271897301#gid=1271897301"
}

def find_resume_index(rows, annotation_key):
    for i, row in enumerate(rows):
        if not str(row.get(annotation_key, "")).strip():
            return i
    return len(rows) - 1

def launch(client):
    email_input = widgets.Text(
        placeholder="Enter your Gmail address",
        description="Your email:",
        layout=widgets.Layout(width="400px"),
        style={"description_width": "initial"}
    )

    login_btn = widgets.Button(
        description="Load my sheet",
        style={"button_color": "#2c3e50"},
        layout=widgets.Layout(height="36px", width="160px")
    )
    login_btn.style.font_weight = "bold"

    login_status = widgets.Output()

    def on_login(b):
        email = email_input.value.strip().lower()
        with login_status:
            clear_output()
            if email not in ANNOTATOR_SHEETS:
                print(f"Email '{email}' not found. Check with your supervisor.")
                return

            try:
                spreadsheet     = client.open_by_url(ANNOTATOR_SHEETS[email])
                sheet           = spreadsheet.worksheet(WORKSHEET_NAME)
                rows            = sheet.get_all_records()
                keys            = list(rows[0].keys()) if rows else []
                annotation_key  = keys[ANNOTATION_COL - 1]
                annotation_key2 = keys[ANNOTATION_COL2 - 1]
                text_key        = keys[1]
                current_ref     = [find_resume_index(rows, annotation_key)]

                print(f"Loaded {len(rows)} rows — resuming from record {current_ref[0] + 1}")

                clear_output(wait=True)
                display(_make_ui(sheet, rows, annotation_key, annotation_key2,
                                 text_key, email, current_ref))
            except Exception as e:
                print(f"Error loading sheet: {e}")

    login_btn.on_click(on_login)
    display(widgets.VBox([
        widgets.HTML("""
            <div style="background:#2c3e50; padding:16px; border-radius:8px; margin-bottom:12px">
                <h2 style="color:white; margin:0; font-family:Helvetica">Annotation Tool</h2>
                <p style="color:#bdc3c7; margin:4px 0 0 0; font-family:Helvetica">
                    Enter your email to load your assigned sheet.
                </p>
            </div>
        """),
        email_input,
        login_btn,
        login_status
    ]))

def _make_ui(sheet, rows, annotation_key, annotation_key2,
             text_key, annotator_name, current_ref):

    total = len(rows)
    done  = sum(1 for r in rows if str(r.get(annotation_key, "")).strip())

    header = widgets.HTML(value=f"""
        <div style="background:#2c3e50; padding:16px; border-radius:8px; margin-bottom:12px">
            <h2 style="color:white; margin:0; font-family:Helvetica">
                Annotation Tool — {annotator_name}
            </h2>
            <p style="color:#bdc3c7; margin:4px 0 0 0; font-family:Helvetica">
                Record {current_ref[0] + 1} of {total} &nbsp;•&nbsp; {done} annotated
            </p>
        </div>
    """)

    # ── Post text ─────────────────────────────────────────────────
    post_text = widgets.HTML(value=f"""
        <div style="background:#f0f0f0; border:1px solid #ddd; border-radius:6px;
                    padding:16px; margin-bottom:12px; font-family:Helvetica;
                    font-size:14px; color:#1a1a1a; line-height:1.6">
            <b style="color:#2c3e50">Post</b><br><br>
            {rows[current_ref[0]].get(text_key, "")}
        </div>
    """)

    # ── Level 1 ───────────────────────────────────────────────────
    l1_label = widgets.HTML(value="""
        <b style="font-family:Helvetica; color:#2c3e50">Level 1 — Select one</b>
    """)

    existing1 = str(rows[current_ref[0]].get(annotation_key, "")).strip()
    radio = widgets.RadioButtons(
        options=LEVEL1_LABELS,
        value=existing1 if existing1 in LEVEL1_LABELS else None,
        layout=widgets.Layout(margin="4px 0 12px 0")
    )

    # ── Level 2 ───────────────────────────────────────────────────
    l2_label = widgets.HTML(value="""
        <div style="background:#fffbe6; padding:8px 12px 4px 12px; border-radius:6px">
            <b style="font-family:Helvetica; color:#2c3e50">Level 2 — Select all that apply</b>
        </div>
    """)

    existing2      = str(rows[current_ref[0]].get(annotation_key2, "")).strip()
    existing2_list = [s.strip() for s in existing2.split(",")] if existing2 else []

    checkboxes = {
        label: widgets.Checkbox(
            value=label in existing2_list,
            description=label,
            style={"description_width": "initial"},
            layout=widgets.Layout(margin="0 16px 0 0")
        )
        for label in LEVEL2_LABELS
    }

    cb_box = widgets.HBox(
        list(checkboxes.values()),
        layout=widgets.Layout(flex_wrap="wrap", padding="8px 12px")
    )

    l2_box = widgets.VBox(
        [l2_label, cb_box],
        layout=widgets.Layout(
            border="1px solid #ffe082",
            border_radius="6px",
            margin="0 0 12px 0",
            display="flex" if existing1 in LEVEL2_TRIGGER else "none"
        )
    )

    def on_level1_change(change):
        if change["new"] in LEVEL2_TRIGGER:
            l2_box.layout.display = "flex"
        else:
            l2_box.layout.display = "none"
            for cb in checkboxes.values():
                cb.value = False

    radio.observe(on_level1_change, names="value")

    # ── Buttons ───────────────────────────────────────────────────
    save_btn = widgets.Button(
        description="✓  Save and continue",
        style={"button_color": "#2c3e50"},
        layout=widgets.Layout(height="40px", width="200px")
    )
    save_btn.style.font_weight = "bold"

    skip_btn = widgets.Button(
        description="Skip (no label)",
        style={"button_color": "#cccccc"},
        layout=widgets.Layout(height="40px", width="160px")
    )

    status = widgets.Output()

    def save(b):
        level1 = radio.value
        if not level1:
            with status:
                clear_output()
                print("Please select a Level 1 label.")
            return

        level2 = ""
        if level1 in LEVEL2_TRIGGER:
            level2 = ", ".join(l for l, cb in checkboxes.items() if cb.value)
            if not level2:
                with status:
                    clear_output()
                    print("Please select at least one Level 2 label.")
                return

        sheet_row = current_ref[0] + 2
        sheet.update_cell(sheet_row, ANNOTATION_COL, level1)
        rows[current_ref[0]][annotation_key] = level1

        if level2:
            sheet.update_cell(sheet_row, ANNOTATION_COL2, level2)
            rows[current_ref[0]][annotation_key2] = level2

        current_ref[0] += 1
        _advance(sheet, rows, annotation_key, annotation_key2,
                 text_key, annotator_name, current_ref)

    def skip(b):
        sheet_row = current_ref[0] + 2
        sheet.update_cell(sheet_row, ANNOTATION_COL, "skip")
        rows[current_ref[0]][annotation_key] = "skip"
        current_ref[0] += 1
        _advance(sheet, rows, annotation_key, annotation_key2,
                 text_key, annotator_name, current_ref)

    save_btn.on_click(save)
    skip_btn.on_click(skip)

    btn_row = widgets.HBox(
        [save_btn, skip_btn],
        layout=widgets.Layout(gap="12px")
    )

    return widgets.VBox(
        [header, post_text, l1_label, radio, l2_box, btn_row, status],
        layout=widgets.Layout(max_width="750px", padding="8px")
    )

def _advance(sheet, rows, annotation_key, annotation_key2,
             text_key, annotator_name, current_ref):
    clear_output(wait=True)
    if current_ref[0] < len(rows):
        display(_make_ui(sheet, rows, annotation_key, annotation_key2,
                         text_key, annotator_name, current_ref))
    else:
        display(widgets.HTML("""
            <div style="background:#2c3e50; padding:24px;
                        border-radius:8px; text-align:center">
                <h2 style="color:white; font-family:Helvetica">
                    🎉 All records completed! Great work.
                </h2>
            </div>
        """))



