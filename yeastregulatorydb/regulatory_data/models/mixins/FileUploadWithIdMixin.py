import logging
from typing import Optional, Protocol, cast

from django.core.files.storage import default_storage
from django.db.models.base import ModelBase

logger = logging.getLogger(__name__)


class FileUploadMetaclass(ModelBase, type):
    pass


class HasPkProtocol(Protocol):
    """
    from copilot: In Python's typing system, a `Protocol` is a way to define an
    interface that a class must adhere to. It's a way to say "any class that
    uses this protocol must have these methods or attributes". In this case,
    `HasPkProtocol` is a protocol that requires a `pk` attribute. The line
    `pk: Optional[int]` is saying that any class that uses this protocol
    must have a `pk` attribute, and that attribute can be an integer or
    `None`. When `FileUploadMixin` inherits from `HasPkProtocol`,
    it's saying that `FileUploadMixin` expects to be used with classes that
    have a `pk` attribute. This doesn't enforce anything at runtime, but it
    gives hints to static type checkers like mypy. So, when you use
    `FileUploadMixin` as a mixin for a Django model, mypy will understand
    that the `pk` attribute is expected to be there, because Django models do
    have a `pk` attribute. This helps to eliminate the error messages you were
    seeing from mypy.
    """

    pk: Optional[int]


class FileUploadMixin(metaclass=FileUploadMetaclass):
    """
    A mixin for models that have a file field that should be uploaded to a
    specific directory and renamed based on the instance's ID. This mixin
    requires that the model have a FileField with an `upload_to` argument

    Example usage:

    .. code-block:: python

        class Hu_s3(BaseModel, FileUploadMixin):
        # Temporary upload path
        file = models.FileField(upload_to='temp', help_text="A gziped csv...")

        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            self.update_file_name('file', 'hu', 'tsv.gz')
            super().save(update_fields=['file'])

        # Other fields and methods...

    """

    def update_file_name(self, file_field_name: str, upload_dir: str, extension: str) -> None:
        """
        A utility method to update the file name based on the instance's ID.
        This method should be called in the `save` method of the model.

        :param file_field_name: The name of the file field to update.
        :type file_field_name: str
        :param upload_dir: The directory to upload the file to.
        :type upload_dir: str
        :param extension: The file extension to use.
        :type extension: str

        :return: None
        :rtype: None
        """
        # Cast self to HasPkProtocol to assure mypy that self has a pk attribute
        self_with_pk = cast(HasPkProtocol, self)
        # raise AttributeError if self does not have a pk attribute
        if not self_with_pk.pk:
            raise AttributeError(f"{self} does not have a pk attribute")
        logger.debug("Updating file name for %s to " "%s/%s.%s", self_with_pk, upload_dir, self_with_pk.pk, extension)
        file_field = getattr(self, file_field_name, None)
        if file_field and self_with_pk.pk and file_field.name:
            # Define new filename with ID
            new_filename = f"{upload_dir}/{self_with_pk.pk}.{extension}"

            # Move and rename the file if it exists
            if default_storage.exists(file_field.name):
                default_storage.save(new_filename, file_field)
                default_storage.delete(file_field.name)

            # Update the file field to new path
            file_field.name = new_filename
            setattr(self, file_field_name, file_field)
