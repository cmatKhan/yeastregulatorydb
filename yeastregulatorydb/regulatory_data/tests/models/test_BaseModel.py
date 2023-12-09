from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase

# from yeastregulatorydb.regulatory_data.models.BaseModel import BaseModel
# from yeastregulatorydb.users.tests.factories import UserFactory


# class ConcreteModel(BaseModel):
#     # Define the fields and additional functionality for your concrete model
#     field1 = models.CharField(max_length=10)

# class BaseModelTestCase(TestCase):
#     def setUp(self):
#         self.user = UserFactory.create(username='testuser')
#         self.model = ConcreteModel.objects.create(uploader=self.user, modifiedBy=self.user)

#     def test_base_model_fields(self):
#         self.assertEqual(self.model.uploader, self.user)
#         self.assertIsNotNone(self.model.uploadDate)
#         self.assertIsNotNone(self.model.modified)
#         self.assertEqual(self.model.modifiedBy, self.user)

#     def test_base_model_auto_update(self):
#         old_modified = self.model.modified
#         self.model.save()  # Save the model to trigger the auto_now field update
#         self.assertNotEqual(self.model.modified, old_modified)

#     def test_base_model_inheritance(self):
#         class MyModel(BaseModel):
#             field1 = models.CharField(max_length=100)
#             field2 = models.IntegerField()

#         my_model = MyModel.objects.create(uploader=self.user, modifiedBy=self.user, field1="value1", field2=42)
#         self.assertEqual(my_model.field1, "value1")
#         self.assertEqual(my_model.field2, 42)
