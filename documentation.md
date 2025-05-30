
# Mosaical Platform Documentation 📚

## Table of Contents
1. [Platform Overview](#platform-overview)
2. [User Guide](#user-guide)
3. [Technical Documentation](#technical-documentation)
4. [API Reference](#api-reference)
5. [AI & Machine Learning](#ai--machine-learning)
6. [Security & Risk Management](#security--risk-management)
7. [Administration](#administration)
8. [Troubleshooting](#troubleshooting)

## Platform Overview

### What is Mosaical?
Mosaical is a DeFi platform specifically designed for GameFi players who want to unlock liquidity from their NFT assets without selling them. The platform combines traditional lending mechanisms with innovative yield generation and AI-powered market intelligence.

### Core Concepts

#### NFT Vault System
- **Purpose**: Secure storage and management of GameFi NFTs
- **Features**: Deposit, withdraw, collateralize, and track NFT performance
- **Security**: Multi-signature protection and automated risk management

#### vBTC (Virtual Bitcoin)
- **Definition**: Platform's native currency for lending and transactions
- **Use Cases**: Loan principal, yield payments, DPO token trading
- **Exchange**: Can be converted to real cryptocurrency (future feature)

#### Dynamic Yields
- **Source**: Generated from GameFi activities and platform fees
- **Distribution**: Automatically calculated and distributed based on NFT utility scores
- **Optimization**: AI algorithms maximize yield potential

#### DPO (Dynamic Partial Ownership) Tokens
- **Concept**: Fractionalized ownership of NFTs
- **Trading**: Marketplace for buying/selling ownership percentages
- **Benefits**: Diversification and increased liquidity

## User Guide

### Getting Started

#### 1. Account Creation
```
1. Visit the registration page
2. Choose a unique username
3. Create a secure password
4. Complete account verification
5. Access your dashboard
```

#### 2. First Steps
```
1. Complete the onboarding tutorial
2. Claim free vBTC from the faucet (if available)
3. Deposit your first NFT
4. Explore the platform features
```

### Managing NFTs

#### Depositing NFTs
1. **Navigate to "Deposit NFT"**
2. **Select Collection**: Choose from supported GameFi collections
3. **Enter Details**:
   - Token ID
   - NFT Name
   - Estimated Value (in vBTC)
   - Utility Score (0-100)
4. **Confirm Deposit**
5. **Verification**: NFT appears in your vault

#### NFT Status Types
- **Deposited**: Available for lending or trading
- **Collateralized**: Currently backing an active loan
- **Partial Liquidated**: Partially sold due to loan default
- **Liquidated**: Fully liquidated due to loan default
- **Withdrawn**: Removed from the platform

### Lending & Borrowing

#### Creating a Loan
1. **Select NFT**: Choose deposited NFT as collateral
2. **Loan Amount**: Enter desired vBTC amount (within LTV limits)
3. **Review Terms**:
   - Interest Rate
   - Loan-to-Value Ratio
   - Liquidation Threshold
4. **Confirm**: Loan is created and vBTC is credited

#### Loan Management
- **Repayment**: Partial or full repayment options
- **Refinancing**: Adjust terms based on market conditions
- **Collateral Swap**: Switch to different NFT collateral
- **Health Monitoring**: Track loan health and liquidation risk

#### Liquidation Process
- **Trigger**: LTV ratio exceeds safe threshold (typically 85%)
- **Grace Period**: 24-hour window for user action
- **Execution**: Automated sale of collateral to cover debt
- **Recovery**: Any remaining value returned to user

### DPO Token Trading

#### Creating DPO Tokens
1. **Select NFT**: Choose from your deposited NFTs
2. **Ownership Percentage**: Define fraction to tokenize (1-99%)
3. **Initial Price**: Set starting price in vBTC
4. **List for Sale**: Make available in marketplace

#### Trading DPO Tokens
- **Browse Marketplace**: View available DPO tokens
- **Purchase**: Buy ownership percentages
- **Price Updates**: Adjust prices for your tokens
- **Portfolio Management**: Track DPO investments

## Technical Documentation

### System Architecture

#### Backend Components
```
mosaical_platform/
├── models.py          # Data models
├── views.py           # Business logic
├── utils.py           # Helper functions
├── ai_models.py       # ML algorithms
├── valuation_oracle.py # Price oracles
├── middleware.py      # Security layers
└── admin.py          # Admin interface
```

#### Database Schema

##### Core Models
- **UserProfile**: User account and vBTC balance
- **NFTCollection**: GameFi collection metadata
- **NFTVault**: Individual NFT records
- **Loan**: Lending transaction details
- **Transaction**: All platform activities
- **DPOToken**: Fractionalized ownership tokens

##### Relationships
```
User (1:1) UserProfile
User (1:N) NFTVault
User (1:N) Loan
User (1:N) Transaction
NFTVault (1:N) Loan
NFTVault (1:N) DPOToken
```

### Configuration

#### Settings Management
```python
# Key configuration files
- django_project/settings.py  # Main Django settings
- .replit                     # Replit configuration
- requirements.txt            # Python dependencies
```

#### Environment Variables
```
DEBUG=True                    # Development mode
SECRET_KEY=<django-secret>    # Django security key
ALLOWED_HOSTS=*.replit.dev    # Allowed domains
```

### Utilities & Helpers

#### Interest Calculator
```python
from mosaical_platform.utils import InterestCalculator

# Calculate compound interest
interest = InterestCalculator.calculate_compound_interest(
    principal=1000,
    rate=5.0,
    time_months=12
)
```

#### Yield Calculator
```python
from mosaical_platform.utils import YieldCalculator

# Calculate NFT yield
yield_amount = YieldCalculator.calculate_monthly_yield(
    nft=nft_instance,
    base_rate=1.0
)
```

#### Liquidation Engine
```python
from mosaical_platform.utils import LiquidationEngine

# Check liquidation eligibility
should_liquidate = LiquidationEngine.should_liquidate(loan_instance)
```

## API Reference

### Authentication Endpoints

#### User Registration
```http
POST /register/
Content-Type: application/x-www-form-urlencoded

username=newuser&password1=password&password2=password
```

#### User Login
```http
POST /login/
Content-Type: application/x-www-form-urlencoded

username=user&password=password
```

### NFT Management

#### Deposit NFT
```http
POST /deposit_nft/
Content-Type: application/x-www-form-urlencoded

collection=1&token_id=123&name=CoolNFT&estimated_value=10.5&utility_score=75
```

#### Get User NFTs
```http
GET /nft_list/
Authorization: Session
```

### Loan Operations

#### Create Loan
```http
POST /create_loan/
Content-Type: application/x-www-form-urlencoded

nft_id=1&loan_amount=5.0
```

#### Repay Loan
```http
POST /repay_loan/
Content-Type: application/x-www-form-urlencoded

loan_id=1&repay_amount=2.5
```

### AI Predictions

#### Get NFT Price Prediction
```http
POST /test_ai_prediction/<nft_id>/
Content-Type: application/json

Response:
{
  "success": true,
  "predicted_price": 12.45,
  "confidence_interval": {
    "lower": 10.5,
    "upper": 14.4
  }
}
```

## AI & Machine Learning

### Price Prediction Engine

#### Model Architecture
- **Random Forest**: Ensemble method for robust predictions
- **Gradient Boosting**: Sequential learning for pattern recognition  
- **XGBoost**: Advanced gradient boosting (if available)
- **Ensemble Voting**: Weighted combination of model outputs

#### Feature Engineering
```python
Features used for prediction:
- Basic NFT characteristics (price, utility, age)
- Collection metrics (floor price, volume, activity)
- Market conditions (sentiment, volatility, trends)
- DeFi metrics (loan activity, yield rates)
- Temporal features (seasonality, cycles)
```

#### Training Process
```bash
# Train AI models with current data
python manage.py train_ai_models

# Update model predictions
python manage.py update_valuations
```

### Market Intelligence

#### Analytics Components
- **Portfolio Analysis**: User asset performance tracking
- **Market Trends**: Collection and sector analysis
- **Risk Assessment**: Credit scoring and default prediction
- **Yield Optimization**: Return maximization strategies

#### Reports Generated
- Daily market summaries
- Collection performance rankings
- User portfolio insights
- Risk factor analysis

## Security & Risk Management

### Authentication & Authorization

#### User Security
- **Password Hashing**: Django's built-in PBKDF2 algorithm
- **Session Management**: Secure session handling with timeout
- **CSRF Protection**: Cross-site request forgery prevention
- **Rate Limiting**: Protection against brute force attacks

#### Data Protection
- **Input Validation**: Comprehensive form and API validation
- **SQL Injection Prevention**: Django ORM parameterized queries
- **XSS Protection**: Template auto-escaping and CSP headers

### Risk Management

#### Loan Risk Assessment
```python
Risk Factors:
- Loan-to-Value Ratio (LTV)
- NFT price volatility
- Collection liquidity
- Historical default rates
- Market conditions
```

#### Liquidation Triggers
- **LTV Threshold**: Default 85% of collateral value
- **Grace Period**: 24 hours for user response
- **Partial Liquidation**: Sell minimum required amount
- **Full Liquidation**: Complete collateral sale if necessary

#### Monitoring Systems
- **Health Checks**: Automated loan health monitoring
- **Alert System**: Notifications for high-risk positions
- **Audit Logs**: Complete transaction history
- **Performance Metrics**: System performance tracking

## Administration

### Admin Interface

#### Accessing Admin Panel
```
URL: /admin/
Credentials: Superuser account required
```

#### Admin Capabilities
- **User Management**: View and modify user accounts
- **NFT Collections**: Manage supported collections
- **System Settings**: Configure platform parameters
- **Transaction Monitoring**: Track all platform activities
- **AI Model Management**: Train and update ML models

#### Key Admin Tasks
```python
# Create NFT collection
collection = NFTCollection.objects.create(
    name="New Game Assets",
    game_name="Epic Quest",
    max_ltv_ratio=60.0,
    base_yield_rate=1.5
)

# Adjust system settings
setting = SystemSettings.objects.create(
    key="MAX_LOAN_AMOUNT",
    value="1000.0",
    description="Maximum loan amount in vBTC"
)
```

### Management Commands

#### Available Commands
```bash
# Load sample data for testing
python manage.py load_sample_data

# Process yield distributions
python manage.py process_yields

# Update NFT valuations
python manage.py update_valuations

# Run liquidation checks
python manage.py auto_liquidation

# Train AI models
python manage.py train_ai_models
```

### Monitoring & Analytics

#### Performance Metrics
- **Response Times**: API endpoint performance
- **Database Queries**: Query optimization tracking
- **User Activity**: Engagement and usage patterns
- **Error Rates**: System reliability monitoring

#### Business Metrics
- **Total Value Locked (TVL)**: Platform asset value
- **Active Loans**: Outstanding loan count
- **Yield Distribution**: Total yields paid out
- **User Growth**: Registration and retention rates

## Troubleshooting

### Common Issues

#### Login Problems
```
Issue: Cannot login with correct credentials
Solutions:
1. Clear browser cache and cookies
2. Check username/password spelling
3. Reset password if needed
4. Contact administrator for account issues
```

#### NFT Deposit Failures
```
Issue: NFT deposit transaction fails
Solutions:
1. Verify collection is supported
2. Check token ID format
3. Ensure reasonable estimated value
4. Try refreshing the page
```

#### Loan Creation Errors
```
Issue: Cannot create loan against NFT
Solutions:
1. Verify NFT is in "Deposited" status
2. Check loan amount against LTV limits
3. Ensure sufficient platform liquidity
4. Review collection lending parameters
```

#### AI Prediction Errors
```
Issue: Price predictions not working
Solutions:
1. Verify AI models are trained
2. Check NFT has sufficient data
3. Run model training command
4. Contact technical support
```

### Error Codes

#### HTTP Status Codes
- **400**: Bad Request - Invalid input data
- **401**: Unauthorized - Authentication required
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource doesn't exist
- **500**: Internal Server Error - System malfunction

#### Custom Error Messages
```python
LOAN_001: "Insufficient collateral value"
LOAN_002: "LTV ratio exceeds maximum allowed"
LOAN_003: "NFT already collateralized"
NFT_001: "Collection not supported"
NFT_002: "Invalid token ID format"
USER_001: "Account not verified"
```

### Performance Optimization

#### Database Optimization
```python
# Query optimization examples
nfts = NFTVault.objects.select_related('collection', 'owner')
loans = Loan.objects.prefetch_related('nft_collateral')
```

#### Caching Strategies
- **Template Caching**: Cache rendered HTML templates
- **Query Caching**: Cache expensive database queries
- **Static Files**: Optimize CSS/JS delivery
- **Image Optimization**: Compress and serve optimized images

### Support & Maintenance

#### Regular Maintenance Tasks
```bash
# Daily tasks
python manage.py auto_liquidation
python manage.py process_yields

# Weekly tasks
python manage.py update_valuations
python manage.py train_ai_models

# Monthly tasks
- Review system performance
- Update security patches
- Backup database
- Review user feedback
```

#### Backup & Recovery
```bash
# Database backup
python manage.py dumpdata > backup.json

# Database restore
python manage.py loaddata backup.json
```

---

*This documentation is continuously updated. For the latest information, check the project repository.*
