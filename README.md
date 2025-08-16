# MoneyTrack - Revolutionary Personal Finance Management System

A comprehensive web-based personal finance management platform built with Django, featuring real-time multi-bank integration, intelligent analytics, and collaborative financial planning.

## Features

### Core Financial Management
- **Multi-Bank Integration**: Seamless connection with major Sri Lankan banks (NSB, Peoples Bank, Sampath, Commercial Bank)
- **Real-time Account Synchronization**: Live balance updates and transaction monitoring
- **Intelligent Transaction Categorization**: ML-powered automatic expense categorization
- **Advanced Budget Tracking**: Predictive budgeting with variance analysis

### Analytics & Visualization
- **Interactive Dashboard**: Dark-themed command center with financial metrics
- **Trend Analysis**: Monthly income vs expense visualization
- **Categorical Breakdowns**: Spending pattern analysis with pie charts
- **Budget vs Actual Tracking**: Performance monitoring across time periods

### Collaborative Features
- **Shared Ledger System**: Family and roommate expense sharing
- **Contribution Tracking**: Transparent expense allocation
- **Multi-user Budget Management**: Collaborative financial planning

### Advanced Capabilities
- **Machine Learning Analytics**: Spending pattern recognition
- **Predictive Budgeting**: AI-powered financial recommendations
- **Automated Savings Goals**: Goal tracking with progress visualization
- **Comprehensive Reporting**: Exportable financial reports
- **Progressive Web App**: Offline capabilities with native app experience

## Technology Stack

- **Backend**: Django 4.2 (MVT Architecture)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: PostgreSQL
- **Cache/Queue**: Redis, Celery
- **Analytics**: Pandas, NumPy, Scikit-learn
- **Visualization**: Plotly, Chart.js
- **Real-time**: Django Channels, WebSockets

## Security & Compliance

- Bank-level security protocols
- End-to-end encryption
- GDPR compliance
- Multi-factor authentication
- Audit trail logging

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate environment: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure environment variables
6. Run migrations: `python manage.py migrate`
7. Start development server: `python manage.py runserver`

## Quick Start

1. Register account and verify email
2. Connect bank accounts through secure API
3. Set up budget categories and limits
4. Invite family members for shared expenses
5. Explore dashboard analytics and insights

## License

MIT License - See LICENSE file for details
