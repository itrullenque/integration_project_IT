from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Sequence
from sqlalchemy.schema import Identity
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Users(db.Model):
    user_id = db.Column(db.String(255), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_mail = db.Column(db.String(255), nullable=False)

    def dict(self):
        return {
            'user_id': self.user_id,
            'password': self.password,
            'user_name': self.user_name,
            'user_mail': self.user_mail
        }
    
# class Portfolios(db.Model):
#     portfolio_id = db.Column(db.String(255), primary_key=True)
#     user_id = db.Column(db.String(255), db.ForeignKey('users.user_id'), nullable=False)
#     user = relationship('Users', backref='portfolios')

#     def dict(self):
#         return {
#             'portfolio_id': self.portfolio_id,
#             'user_id': self.user_id,
#         }
    
class User_stocks(db.Model):
    stock_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(255), db.ForeignKey('users.user_id'), nullable=False)
    ticker = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user = relationship('Users', backref='user_stocks')

    def dict(self):
        return {
            'stock_id': self.stock_id,
            'user_id': self.user_id,
            'ticker': self.ticker,
            'quantity': self.quantity,
        }
    
