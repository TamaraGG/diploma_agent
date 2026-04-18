from database.base.base import Base
from database.debt_sme_subj.base_model import DebtSubjMixin


class FDebtSmeSubj(Base, DebtSubjMixin):
    __tablename__ = "f_debt_sme_subj"