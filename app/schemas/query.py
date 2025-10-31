from dataclasses import dataclass


@dataclass
class PagedResult[T]:
    page: T
    total: int
