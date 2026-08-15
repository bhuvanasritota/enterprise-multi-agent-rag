from app.services.storage import secure_filename

def test_secure_filename():
    assert secure_filename("../../Employee Policy 2026.pdf") == "Employee_Policy_2026.pdf"
