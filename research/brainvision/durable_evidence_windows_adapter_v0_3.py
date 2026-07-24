from __future__ import annotations

from dataclasses import dataclass


DIRECTORY_DURABILITY_CONFIRMED = "DIRECTORY_DURABILITY_CONFIRMED"
DIRECTORY_DURABILITY_UNCONFIRMED = "DIRECTORY_DURABILITY_UNCONFIRMED"
PROMOTION_CONFIRMED = "PROMOTION_CONFIRMED"
PROMOTION_UNCONFIRMED = "PROMOTION_UNCONFIRMED"


class PlatformPrimitiveUnvalidated(RuntimeError):
    pass


@dataclass(frozen=True)
class DirectoryDurabilityResult:
    status: str
    detail: str


@dataclass(frozen=True)
class DirectoryPromotionResult:
    status: str
    detail: str


class WindowsDurabilityAdapter:
    def sync_directory_entry(self, directory_path: str) -> DirectoryDurabilityResult:
        raise NotImplementedError


class SameVolumeNoReplacePromotionAdapter:
    def promote_verified_directory_no_replace(
        self, source_directory_path: str, destination_directory_path: str
    ) -> DirectoryPromotionResult:
        raise NotImplementedError


class FailClosedWindowsDurabilityAdapter(WindowsDurabilityAdapter):
    def sync_directory_entry(self, directory_path: str) -> DirectoryDurabilityResult:
        return DirectoryDurabilityResult(
            DIRECTORY_DURABILITY_UNCONFIRMED,
            "Windows directory-entry durability primitive is unvalidated.",
        )


class FailClosedSameVolumeNoReplacePromotionAdapter(SameVolumeNoReplacePromotionAdapter):
    def promote_verified_directory_no_replace(
        self, source_directory_path: str, destination_directory_path: str
    ) -> DirectoryPromotionResult:
        return DirectoryPromotionResult(
            PROMOTION_UNCONFIRMED,
            "Same-volume no-replace directory promotion primitive is unvalidated.",
        )
