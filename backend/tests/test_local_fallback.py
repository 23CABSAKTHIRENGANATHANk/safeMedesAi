import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, seed_local_fallback_data
from app.models.medicine import MedicineRecord
from app.services.verify import VerifyService


class LocalFallbackTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()

    def test_seed_and_verify(self):
        seed_local_fallback_data(self.session)
        self.session.commit()

        self.assertGreater(self.session.query(MedicineRecord).count(), 0)

        warning_result = VerifyService.verify(db=self.session, name="Amoxicillin")
        self.assertEqual(warning_result["status"], "warning")

        safe_result = VerifyService.verify(db=self.session, name="Paracetamol")
        self.assertEqual(safe_result["status"], "safe")

        unknown_result = VerifyService.verify(db=self.session, name="TotallyFakeDrug123")
        self.assertEqual(unknown_result["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
