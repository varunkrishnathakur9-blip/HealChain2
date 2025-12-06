# Changelog

## [Frontend Upgrade] - 2024

### Added
- Complete design system with CSS variables and design tokens
- New page components: Dashboard, PublishTask, Mining, Rewards
- Web3 integration with wagmi v2 and viem
- Reusable component library (Button, Card, Badge, ProgressBar, Metric, Nav, WalletConnect)
- Centralized API configuration (`src/config/api.js`)
- Responsive design for mobile, tablet, and desktop
- Comprehensive documentation (README, INTEGRATION, PROJECT_STATUS)

### Changed
- Updated all API calls to use centralized configuration
- Improved error handling in API calls
- Enhanced responsive breakpoints
- Updated navigation to use new design system

### Fixed
- Removed hardcoded API URLs (now configurable via environment variables)
- Fixed responsive table layouts for mobile
- Improved accessibility with proper focus states
- Fixed import paths and component organization

### Removed
- Temporary files (`tempCodeRunnerFile.py` in multiple directories)
- Error log files (`sim_server_error.log`)
- Empty directories

### Security
- Enhanced .gitignore to exclude sensitive files
- Added environment variable support for configuration
- Improved error handling to prevent information leakage

---

## Previous Versions

See git history for earlier changes.

