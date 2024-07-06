from rest_framework import serializers

from ...models import Binding, BindingConcatenated, DataSource, Regulator
from .mixins.CustomValidateMixin import CustomValidateMixin


class BindingConcatenatedSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    bindings = serializers.PrimaryKeyRelatedField(queryset=Binding.objects.all(), many=True)
    regulator = serializers.PrimaryKeyRelatedField(queryset=Regulator.objects.all(), required=True)
    source = serializers.PrimaryKeyRelatedField(queryset=DataSource.objects.all(), required=True)
    regulator_locus_tag = serializers.CharField(source="regulator.genomicfeature.locus_tag", read_only=True)
    regulator_symbol = serializers.CharField(source="regulator.genomicfeature.symbol", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = BindingConcatenated
        fields = "__all__"

    def create_or_update(self, validated_data):
        """
        Create or update a BindingConcatenated record with the given data.

        This method is used by both the `create` and `update` methods to
        handle the creation or updating of a BindingConcatenated record. If a record
        with the same regulator and source already exists, it will be updated.

        :param validated_data: The validated data to use for creating or updating the record
        :type validated_data: dict

        :return: The created or updated BindingConcatenated record
        :rtype: BindingConcatenated
        """
        # Extract bindings data
        bindings_data = validated_data.pop("bindings")
        regulator = validated_data["regulator"]
        source = validated_data["source"]

        # Check for existing record
        existing_record = BindingConcatenated.objects.filter(regulator=regulator, source=source).first()

        # Calculate the inserts
        genomic_inserts = sum(binding.genomic_inserts for binding in bindings_data)
        mito_inserts = sum(binding.mito_inserts for binding in bindings_data)
        plasmid_inserts = sum(binding.plasmid_inserts for binding in bindings_data)

        # Update case
        if existing_record:
            # Update all fields EXCEPT bindings, which
            # must be handled by the .set() method
            # https://docs.djangoproject.com/en/4.2/ref/models/relations/#django.db.models.fields.related.RelatedManager.set
            for attr, value in validated_data.items():
                # do not update the original `uploader` and `upload_date` fields
                if attr not in ["uploader", "upload_date"]:
                    setattr(existing_record, attr, value)
            existing_record.genomic_inserts = genomic_inserts
            existing_record.mito_inserts = mito_inserts
            existing_record.plasmid_inserts = plasmid_inserts
            existing_record.save()
            # See comment above
            existing_record.bindings.set(bindings_data)
            return existing_record
        # Create case
        else:
            # Create case
            binding_concatenated = BindingConcatenated.objects.create(
                genomic_inserts=genomic_inserts,
                mito_inserts=mito_inserts,
                plasmid_inserts=plasmid_inserts,
                **validated_data,
            )
            # see comment in the `if` block above re: set() and ManyToMany fields
            binding_concatenated.bindings.set(bindings_data)
            return binding_concatenated

    def create(self, validated_data):
        return self.create_or_update(validated_data)

    def update(self, instance, validated_data):
        return self.create_or_update(validated_data)
