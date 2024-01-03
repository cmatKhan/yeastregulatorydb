import logging
from typing import Any

from django.db import IntegrityError
from rest_framework import serializers

from ....models import GenomicFeature, Regulator
from ..RegulatorSerializer import RegulatorSerializer

logger = logging.getLogger(__name__)


class GetOrCreateRegulatorMixin:
    """
    This mixin is intended for serializers for models that have a `regulator`
    field which foreign keys to the Regulator model. It extends the
    DRF function to_interval_value() to populate the `regulator` field if
    `regulator_locus_tag` or `regulator_symbol` is provided in the request data.
    """

    def get_regulator_instance(self, data: dict) -> Regulator:
        """
        If `regulator_locus_tag` or `regulator_symbol` are passed in the `data`,
        then try to get the regulator instance based on the locus tag or symbol.
        If the regulator instance does not exist, then create a new regulator
        instance based on the locus tag or symbol.

        :param data: request data
        :type data: dict
        :return: Regulator instance
        :rtype: Regulator

        :raises serializers.ValidationError: if neither `regulator_locus_tag`
            nor `regulator_symbol` are in the request data
        :raises serializers.ValidationError: if both `regulator_locus_tag` and
            `regulator_symbol` are in the request data
        :raises serializers.ValidationError: if the regulator instance created
            based on the locus tag or symbol is invalid
        :raises serializers.ValidationError: if the genomic feature
            corresponding to the locus tag or symbol does not exist
        :raises serializers.ValidationError: if there is a database error while
            creating a new regulator instance
        :raises serializers.ValidationError: if there is a value error while
            creating a new regulator instance
        """
        # if `regulator` is not in the request data, then check that
        # regulator_locus_tag or regulator_symbol, but not both,
        # is in the request data
        if "regulator_locus_tag" not in data and "regulator_symbol" not in data:
            raise serializers.ValidationError(
                "If you do not provide `regulator`, you "
                "must provide either `regulator_locus_tag` or `regulator_symbol`"
            )
        elif "regulator_locus_tag" in data and "regulator_symbol" in data:
            raise serializers.ValidationError(
                "You must provide either regulator_locus_tag or regulator_symbol, not both"
            )
        else:
            # try to get the regulator instance based on the regulator locus tag or symbol
            try:
                if "regulator_locus_tag" in data:
                    regulator_instance = Regulator.objects.get(
                        genomicfeature__locus_tag=data.get("regulator_locus_tag")
                    )
                else:
                    regulator_instance = Regulator.objects.get(genomicfeature__symbol=data.get("regulator_symbol"))
            except Regulator.DoesNotExist:
                logger.info(
                    "Regulator entry for locus identifier %s not found. Trying to create one...",
                    data.get("regulator_locus_tag")
                    if data.get("regulator_locus_tag")
                    else data.get("regulator_symbol"),
                )
                # try to find the genomic instance corresponding to the
                # request `regulator_locus_tag` or `regulator_symbol`
                try:
                    if "regulator_locus_tag" in data:
                        genomic_feature = GenomicFeature.objects.get(locus_tag=data.get("regulator_locus_tag"))
                    else:
                        genomic_feature = GenomicFeature.objects.get(symbol=data.get("regulator_symbol"))
                # if the genomic feature does not exist, then return a 400
                # response
                except GenomicFeature.DoesNotExist:
                    raise serializers.ValidationError(
                        "Genomic Feature not found for locus identifier %s " % data.get("regulator_locus_tag")
                        if data.get("regulator_locus_tag")
                        else data.get("regulator_symbol")
                    )
                # else, try to create a new regulator instance
                else:
                    regulator_serializer = RegulatorSerializer(
                        data={"genomicfeature": genomic_feature.id}, context={"request": self.context.get("request")}
                    )
                    try:
                        # check validity of the regulator data
                        regulator_serializer.is_valid(raise_exception=True)
                    # if the regulator data is invalid, then return a 400
                    except serializers.ValidationError as e:
                        raise serializers.ValidationError(
                            "The Regulator instance created for regulator locus %s is invalid: %s"
                            % (
                                data.get("regulator_locus_tag")
                                if data.get("regulator_locus_tag")
                                else data.get("regulator_symbol"),
                                e,
                            )
                        )
                    except AttributeError as e:
                        raise serializers.ValidationError(
                            "Attribute error while creating a new regulator instance: %s" % e
                        )
                    else:
                        # if the regulator data is valid, then try to create
                        # a new regulator instance. Catch errors and raise
                        # serializer errors if they occur
                        try:
                            regulator_instance = regulator_serializer.save()
                        except IntegrityError as e:
                            raise serializers.ValidationError(
                                "Database error while creating a new regulator instance: %s" % e
                            )
                        except ValueError as e:
                            raise serializers.ValidationError(
                                "Value error while creating a new regulator instance: %s" % e
                            )
        return regulator_instance

    def to_internal_value(self, data: Any) -> Any:
        """
        Override the DRF to_internal_value() method to populate the `regulator`
        """
        if "regulator" not in data:
            data["regulator"] = self.get_regulator_instance(data).pk
            data.pop("regulator_locus_tag", None)
            data.pop("regulator_symbol", None)
        return super().to_internal_value(data)
