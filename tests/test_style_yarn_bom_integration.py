"""
Test script for Style-to-Yarn BOM Integration
Demonstrates the enhanced BOM explosion using cfab_Yarn_Demand_By_Style.csv
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)

import pandas as pd

from engine.style_yarn_bom_integration import StyleYarnBOMIntegrator
from models.bom import BOMExploder


def test_style_yarn_integration():
    """Test the enhanced style-to-yarn BOM integration"""
    
    logger.info("=" * 80)
    logger.info("STYLE-TO-YARN BOM INTEGRATION TEST")
    logger.info("=" * 80)
    
    # Initialize the integrator
    logger.info("\n1. Loading BOM data from cfab_Yarn_Demand_By_Style.csv...")
    integrator = StyleYarnBOMIntegrator()
    
    # Show some statistics
    logger.info(f"\n   ✅ Loaded {len(integrator.style_yarn_mappings)} unique styles")
    logger.info(f"   ✅ Found {len(integrator.yarn_master)} unique yarns")
    
    # Test with sample style forecasts
    logger.info("\n2. Testing with sample style forecasts...")
    style_forecasts = {
        '1853/L': 10000.0,      # 10,000 yards
        '1853/LU': 8000.0,      # 8,000 yards
        '180001/20ST2': 5000.0, # 5,000 yards
        '2027-2.9/B': 3000.0,   # 3,000 yards
        '205FLX2006/B': 7500.0  # 7,500 yards
    }
    
    logger.info("\n   Style Forecasts:")
    for style, qty in style_forecasts.items():
        logger.info(f"   - {style}: {qty:,.0f} yards")
    
    # Explode to yarn requirements
    logger.info("\n3. Exploding style forecasts to yarn requirements...")
    yarn_requirements = integrator.explode_style_forecast_to_yarn(style_forecasts)
    
    # Display results
    logger.info("\n4. Yarn Requirements Summary:")
    logger.info("-" * 80)
    
    total_yarn_required = 0
    for yarn_id, req_data in sorted(yarn_requirements.items()):
        logger.info(f"\n   Yarn ID: {yarn_id}")
        logger.info(f"   Total Required: {req_data['total_qty']:,.2f} {req_data['unit']}")
        logger.info(f"   Sources ({len(req_data['sources'])} styles):")
        
        for source in req_data['sources']:
            logger.info(f"     - Style {source['style_id']}: {source['yarn_qty']:,.2f} yards "
                  f"({source['percentage']:.1f}% of {source['style_qty']:,.0f} yards)")
        
        total_yarn_required += req_data['total_qty']
    
    logger.info("\n" + "-" * 80)
    logger.info(f"TOTAL YARN REQUIRED: {total_yarn_required:,.2f} yards")
    
    # Test yarn composition lookup
    logger.info("\n5. Testing yarn composition lookup...")
    test_style = '180001/20ST2'
    composition = integrator.get_yarn_composition_for_style(test_style)
    logger.info(f"\n   Yarn composition for style {test_style}:")
    for yarn_id, percentage in composition:
        logger.info(f"   - Yarn {yarn_id}: {percentage:.1f}%")
    
    # Test styles using yarn lookup
    logger.info("\n6. Testing styles using yarn lookup...")
    test_yarn = '18707'
    styles = integrator.get_styles_using_yarn(test_yarn)
    logger.info(f"\n   Styles using yarn {test_yarn}:")
    for style in styles[:5]:  # Show first 5
        logger.info(f"   - {style}")
    if len(styles) > 5:
        logger.info(f"   ... and {len(styles) - 5} more styles")
    
    # Test unit conversion
    logger.info("\n7. Testing unit conversions...")
    test_conversions = [
        (1000, 'yards', 'meters'),
        (500, 'meters', 'yards'),
        (100, 'pounds', 'kilograms'),
        (50, 'kilograms', 'pounds')
    ]
    
    for qty, from_unit, to_unit in test_conversions:
        converted = integrator.convert_units(qty, from_unit, to_unit)
        logger.info(f"   {qty} {from_unit} = {converted:.2f} {to_unit}")
    
    # Generate BOM report
    logger.info("\n8. Generating BOM summary report...")
    report_df = integrator.generate_bom_report()
    logger.info(f"\n   Report contains {len(report_df)} BOM entries")
    logger.info("\n   Sample entries:")
    logger.info(report_df.head(10).to_string(index=False))
    
    # Save detailed results
    logger.info("\n9. Saving detailed results...")
    
    # Save yarn requirements
    with open('test_yarn_requirements.json', 'w') as f:
        # Convert to serializable format
        serializable_reqs = {}
        for yarn_id, req_data in yarn_requirements.items():
            serializable_reqs[yarn_id] = {
                'total_qty': req_data['total_qty'],
                'unit': req_data['unit'],
                'sources': req_data['sources'],
                'weekly_breakdown': req_data.get('weekly_breakdown', {})
            }
        json.dump(serializable_reqs, f, indent=2)
    
    # Save BOM report
    report_df.to_csv('test_bom_report.csv', index=False)
    
    logger.info("\n   ✅ Saved yarn requirements to test_yarn_requirements.json")
    logger.info("   ✅ Saved BOM report to test_bom_report.csv")
    
    return yarn_requirements


def test_comparison_with_original():
    """Compare enhanced integration with original BOM explosion"""
    
    logger.info("\n" + "=" * 80)
    logger.info("COMPARISON: Enhanced vs Original BOM Explosion")
    logger.info("=" * 80)
    
    # Test data
    style_forecasts = {
        '1853/L': 5000.0,
        '180001/20ST2': 3000.0
    }
    
    # Enhanced method
    logger.info("\n1. Enhanced Integration Method:")
    integrator = StyleYarnBOMIntegrator()
    enhanced_results = integrator.explode_style_forecast_to_yarn(style_forecasts)
    
    enhanced_total = sum(req['total_qty'] for req in enhanced_results.values())
    logger.info(f"   Total yarn required: {enhanced_total:,.2f} yards")
    logger.info(f"   Number of yarns: {len(enhanced_results)}")
    
    # Original method
    logger.info("\n2. Original BOM Explosion Method:")
    bom_df = pd.read_csv('data/cfab_Yarn_Demand_By_Style.csv')
    style_yarn_boms = BOMExploder.from_style_yarn_dataframe(bom_df)
    original_results = BOMExploder.explode_style_to_yarn_requirements(style_forecasts, style_yarn_boms)
    
    # Remove validation warnings if present
    if '_validation_warnings' in original_results:
        del original_results['_validation_warnings']
    
    original_total = sum(req['total_qty'] for req in original_results.values())
    logger.info(f"   Total yarn required: {original_total:,.2f} yards")
    logger.info(f"   Number of yarns: {len(original_results)}")
    
    # Compare results
    logger.info("\n3. Comparison:")
    logger.info(f"   Difference in total quantity: {abs(enhanced_total - original_total):.2f} yards")
    logger.info(f"   Difference in yarn count: {abs(len(enhanced_results) - len(original_results))}")
    
    # Check for discrepancies
    all_yarns = set(enhanced_results.keys()) | set(original_results.keys())
    discrepancies = []
    
    for yarn_id in all_yarns:
        enhanced_qty = enhanced_results.get(yarn_id, {}).get('total_qty', 0)
        original_qty = original_results.get(yarn_id, {}).get('total_qty', 0)
        
        if abs(enhanced_qty - original_qty) > 0.01:
            discrepancies.append({
                'yarn_id': yarn_id,
                'enhanced_qty': enhanced_qty,
                'original_qty': original_qty,
                'difference': enhanced_qty - original_qty
            })
    
    if discrepancies:
        logger.info(f"\n   ⚠️  Found {len(discrepancies)} discrepancies:")
        for disc in discrepancies[:5]:
            logger.info(f"      Yarn {disc['yarn_id']}: Enhanced={disc['enhanced_qty']:.2f}, "
                  f"Original={disc['original_qty']:.2f}, Diff={disc['difference']:.2f}")
    else:
        logger.info("\n   ✅ Results match between both methods!")


if __name__ == "__main__":
    # Run the main test
    yarn_requirements = test_style_yarn_integration()
    
    # Run comparison test
    test_comparison_with_original()
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)