from django import forms


class MultiFileInput(forms.FileInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs["multiple"] = "multiple"
        return super().render(name, value, attrs)


class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV")
    files = forms.FileField(widget=MultiFileInput(), label="Upload Files")
