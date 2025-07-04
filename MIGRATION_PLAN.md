# Repository Structure Migration Plan

## Current State Analysis

### Active Production System
- **Location**: `twitter/` directory
- **Entry Point**: `start_webhook_bot.sh` -> `twitter/webhook_bot.py`
- **Dependencies**: 
  - `twitter/storage_utils.py` (enhanced with media download)
  - `twitter/scrape_tweet.py` (tweet processing)
  - `twitter/accounts.db` (active database)

### New Modular System  
- **Location**: `platforms/twitter/` directory
- **Implementation**: Modern class-based scraper
- **Status**: Implemented but not integrated with active bot

## Issues Identified

1. **Duplicate Twitter Implementations**
   - Legacy: `twitter/` (196KB, production active)
   - Modern: `platforms/twitter/` (20KB, not integrated)

2. **Script Organization**
   - ✅ **FIXED**: Database scripts moved to `scripts/database/`
   - ✅ **FIXED**: Test scripts moved to `scripts/testing/`
   - ✅ **FIXED**: Utilities organized in `scripts/utilities/` and `services/`

3. **Legacy Platform Directories**
   - ✅ **FIXED**: Empty `facebook/`, `instagram/`, `tiktok/` directories removed

## Migration Options

### Option A: Gradual Migration (Recommended - SAFE)
1. **Phase 1**: ✅ Clean up obvious redundancies (COMPLETED)
2. **Phase 2**: Update documentation and mark legacy vs modern systems
3. **Phase 3**: Plan integration testing for modular system
4. **Phase 4**: Gradual migration with fallback capability

### Option B: Immediate Migration (HIGH RISK)
1. Update all import paths to use modular system
2. Migrate webhook_bot.py to use `core/` and `platforms/` 
3. Test thoroughly in development
4. Deploy with potential downtime

## Recommended Actions

### Immediate (Safe)
- ✅ Document current vs future architecture
- ✅ Keep production system stable in `twitter/`
- ✅ Continue development on modular system in `platforms/`

### Next Phase (Planned)
- Create integration tests for modular system
- Develop migration scripts for import path updates
- Plan testing phase with duplicate systems running
- Schedule migration window for production switch

## Current Directory Structure (Post-Cleanup)

```
social-media-archive-project/
├── twitter/                 # ACTIVE PRODUCTION SYSTEM
│   ├── webhook_bot.py      # Main bot application
│   ├── storage_utils.py    # Enhanced storage manager
│   ├── scrape_tweet.py     # Tweet processing
│   └── accounts.db         # Active database
├── platforms/              # NEW MODULAR SYSTEM
│   └── twitter/
│       └── scraper.py      # Modern scraper class
├── core/                   # Shared modular components
│   ├── media_downloader.py
│   ├── storage_manager.py
│   └── data_models.py
├── scripts/                # Organized scripts
│   ├── database/          # Database utilities
│   ├── testing/           # Test scripts
│   └── utilities/         # Utility scripts
└── services/              # Service components
    └── serve_media.py     # Media server
```

## Risk Assessment

### LOW RISK (Current Approach)
- Keep production system unchanged
- Continue development on modular system
- Thorough testing before any production changes

### HIGH RISK (Immediate Migration)
- Service interruption possible
- Import path conflicts
- Untested integration points

## Conclusion

The gradual migration approach allows us to:
1. Maintain stable production service
2. Continue improving the modular architecture
3. Plan thorough testing and validation
4. Minimize risk of service disruption

Current cleanup has organized the repository while preserving the working production system.
