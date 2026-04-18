from database.base.base import Base
from database.debt_sme_subj.base_model import DebtSubjMixin


class IDebtSmeSubj(Base, DebtSubjMixin):
    __tablename__ = "i_debt_sme_subj"
