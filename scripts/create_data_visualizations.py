"""
Beverly Knits Data Relationship Visualizer
==========================================
Creates visual diagrams showing how all CSV files are related
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np


def create_data_relationship_diagram():
    """Create a visual diagram showing all data relationships"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define box positions and properties
    boxes = {
        'sales_orders': {'pos': (1, 8), 'color': '#FFE5B4', 'label': 'Sales Orders\n(eFab_SO_List)'},
        'sales_history': {'pos': (1, 6.5), 'color': '#FFE5B4', 'label': 'Sales History\n(Sales Activity Report)'},
        'style_bom': {'pos': (3, 7.25), 'color': '#B4E5FF', 'label': 'Style BOM\n(Style_BOM)'},
        'yarn_demand_style': {'pos': (5, 8), 'color': '#FFB4B4', 'label': 'Yarn Demand by Style\n(cfab_Yarn_Demand)'},
        'yarn_master': {'pos': (7, 7.25), 'color': '#B4FFB4', 'label': 'Yarn Master\n(Yarn_ID)'},
        'yarn_inventory': {'pos': (9, 8), 'color': '#B4FFB4', 'label': 'Yarn Inventory\n(Yarn_ID_Current)'},
        'inventory_upload': {'pos': (9, 6.5), 'color': '#B4FFB4', 'label': 'Inventory Upload\n(inventory.csv)'},
        'suppliers': {'pos': (7, 5.5), 'color': '#FFB4FF', 'label': 'Suppliers\n(Supplier_ID)'},
        'yarn_demand_weekly': {'pos': (5, 5.5), 'color': '#FFB4B4', 'label': 'Weekly Yarn Demand\n(Yarn_Demand_2025)'},
        
        # Integration outputs
        'integrated_yarn': {'pos': (5, 3.5), 'color': '#D3D3D3', 'label': 'Integrated\nYarn Master'},
        'total_demand': {'pos': (3, 3.5), 'color': '#D3D3D3', 'label': 'Total\nYarn Demand'},
        'net_requirements': {'pos': (5, 2), 'color': '#D3D3D3', 'label': 'Net\nRequirements'},
        'procurement_plan': {'pos': (5, 0.5), 'color': '#90EE90', 'label': 'Procurement\nPlan'},
    }
    
    # Draw boxes
    for key, props in boxes.items():
        box = FancyBboxPatch(
            (props['pos'][0] - 0.6, props['pos'][1] - 0.3),
            1.2, 0.6,
            boxstyle="round,pad=0.1",
            facecolor=props['color'],
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(box)
        ax.text(props['pos'][0], props['pos'][1], props['label'], 
                ha='center', va='center', fontsize=10, weight='bold')
    
    # Define relationships
    relationships = [
        # Primary data relationships
        ('sales_orders', 'style_bom', 'Style_ID'),
        ('sales_history', 'style_bom', 'Style_ID'),
        ('style_bom', 'yarn_demand_style', 'Style_ID'),
        ('style_bom', 'yarn_master', 'Yarn_ID'),
        ('yarn_demand_style', 'yarn_master', 'Yarn_ID'),
        ('yarn_master', 'yarn_inventory', 'Yarn_ID'),
        ('yarn_master', 'inventory_upload', 'Yarn_ID'),
        ('yarn_master', 'suppliers', 'Supplier'),
        ('yarn_demand_weekly', 'yarn_master', 'Yarn_ID'),
        
        # Integration flows
        ('yarn_master', 'integrated_yarn', 'merge'),
        ('yarn_inventory', 'integrated_yarn', 'merge'),
        ('inventory_upload', 'integrated_yarn', 'merge'),
        ('suppliers', 'integrated_yarn', 'merge'),
        
        ('style_bom', 'total_demand', 'calculate'),
        ('yarn_demand_style', 'total_demand', 'calculate'),
        
        ('integrated_yarn', 'net_requirements', 'calculate'),
        ('total_demand', 'net_requirements', 'calculate'),
        
        ('net_requirements', 'procurement_plan', 'generate'),
    ]
    
    # Draw relationships
    for source, target, label in relationships:
        source_pos = boxes[source]['pos']
        target_pos = boxes[target]['pos']
        
        # Determine connection style
        if label in ['merge', 'calculate', 'generate']:
            arrow_style = '->'
            color = 'green'
            linestyle = '--'
        else:
            arrow_style = '->'
            color = 'blue'
            linestyle = '-'
        
        arrow = ConnectionPatch(
            source_pos, target_pos, "data", "data",
            arrowstyle=arrow_style,
            shrinkA=35, shrinkB=35,
            mutation_scale=20,
            fc=color,
            ec=color,
            linestyle=linestyle,
            linewidth=2
        )
        ax.add_artist(arrow)
        
        # Add label
        mid_x = (source_pos[0] + target_pos[0]) / 2
        mid_y = (source_pos[1] + target_pos[1]) / 2
        ax.text(mid_x, mid_y, label, fontsize=8, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # Add title and legend
    ax.text(5, 9.5, 'Beverly Knits Data Integration Map', 
            fontsize=16, weight='bold', ha='center')
    
    # Add legend
    legend_elements = [
        patches.Patch(color='#FFE5B4', label='Sales Data'),
        patches.Patch(color='#B4E5FF', label='Product Data'),
        patches.Patch(color='#FFB4B4', label='Demand Data'),
        patches.Patch(color='#B4FFB4', label='Inventory Data'),
        patches.Patch(color='#FFB4FF', label='Supplier Data'),
        patches.Patch(color='#D3D3D3', label='Integrated Data'),
        patches.Patch(color='#90EE90', label='Output'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    plt.savefig('data_relationship_diagram.png', dpi=300, bbox_inches='tight')
    plt.show()


def create_data_flow_diagram():
    """Create a diagram showing the data processing flow"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define process steps
    steps = [
        {'pos': (5, 9), 'label': '1. Load Raw Data\n(9 CSV files)', 'color': '#FFE5B4'},
        {'pos': (5, 7.5), 'label': '2. Clean & Standardize\n(Handle nulls, normalize IDs)', 'color': '#FFD700'},
        {'pos': (5, 6), 'label': '3. Create Relationships\n(Join on keys)', 'color': '#FFA500'},
        {'pos': (2.5, 4.5), 'label': '4a. Calculate Demand\n(BOM explosion)', 'color': '#FF6347'},
        {'pos': (7.5, 4.5), 'label': '4b. Aggregate Inventory\n(Current + On Order)', 'color': '#FF6347'},
        {'pos': (5, 3), 'label': '5. Net Requirements\n(Demand - Supply)', 'color': '#DC143C'},
        {'pos': (5, 1.5), 'label': '6. Apply Constraints\n(MOQ, Lead Time, Safety)', 'color': '#8B0000'},
        {'pos': (5, 0.5), 'label': '7. Generate Plan\n(Procurement Orders)', 'color': '#90EE90'},
    ]
    
    # Draw process boxes
    for i, step in enumerate(steps):
        box = FancyBboxPatch(
            (step['pos'][0] - 1, step['pos'][1] - 0.4),
            2, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=step['color'],
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(box)
        ax.text(step['pos'][0], step['pos'][1], step['label'], 
                ha='center', va='center', fontsize=11, weight='bold')
    
    # Draw flow arrows
    flows = [
        (0, 1), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5), (5, 6), (6, 7)
    ]
    
    for start_idx, end_idx in flows:
        if start_idx < len(steps) and end_idx < len(steps):
            start_pos = steps[start_idx]['pos']
            end_pos = steps[end_idx]['pos']
            
            arrow = ConnectionPatch(
                start_pos, end_pos, "data", "data",
                arrowstyle='->',
                shrinkA=40, shrinkB=40,
                mutation_scale=20,
                fc='black',
                linewidth=2
            )
            ax.add_artist(arrow)
    
    # Add annotations
    ax.text(1, 8.5, 'Input Files:', fontsize=10, weight='bold')
    ax.text(1, 8.2, '• Sales Orders', fontsize=9)
    ax.text(1, 7.9, '• Style BOM', fontsize=9)
    ax.text(1, 7.6, '• Yarn Master', fontsize=9)
    ax.text(1, 7.3, '• Inventory', fontsize=9)
    ax.text(1, 7.0, '• Suppliers', fontsize=9)
    
    ax.text(8.5, 1.5, 'Outputs:', fontsize=10, weight='bold')
    ax.text(8.5, 1.2, '• Purchase Orders', fontsize=9)
    ax.text(8.5, 0.9, '• Urgency Flags', fontsize=9)
    ax.text(8.5, 0.6, '• Cost Analysis', fontsize=9)
    ax.text(8.5, 0.3, '• Lead Times', fontsize=9)
    
    # Add title
    ax.text(5, 9.8, 'Beverly Knits Data Processing Flow', 
            fontsize=16, weight='bold', ha='center')
    
    plt.tight_layout()
    plt.savefig('data_flow_diagram.png', dpi=300, bbox_inches='tight')
    plt.show()


def create_integration_summary_table():
    """Create a summary table of all data integrations"""
    
    integration_summary = pd.DataFrame([
        {
            'Source File': 'eFab_SO_List.csv',
            'Target File': 'Style_BOM.csv',
            'Join Key': 'cFVersion → Style_ID',
            'Purpose': 'Link orders to product specifications'
        },
        {
            'Source File': 'Style_BOM.csv',
            'Target File': 'Yarn_ID.csv',
            'Join Key': 'Yarn_ID',
            'Purpose': 'Get yarn details for each style'
        },
        {
            'Source File': 'cfab_Yarn_Demand_By_Style.csv',
            'Target File': 'Yarn_ID.csv',
            'Join Key': 'Yarn → Yarn_ID',
            'Purpose': 'Match demand to yarn specifications'
        },
        {
            'Source File': 'Yarn_ID.csv',
            'Target File': 'Supplier_ID.csv',
            'Join Key': 'Supplier',
            'Purpose': 'Get supplier constraints (MOQ, lead time)'
        },
        {
            'Source File': 'Yarn_ID_Current_Inventory.csv',
            'Target File': 'inventory.csv',
            'Join Key': 'Yarn_ID → material_id',
            'Purpose': 'Reconcile inventory sources'
        },
        {
            'Source File': 'Sales Activity Report.csv',
            'Target File': 'Style_BOM.csv',
            'Join Key': 'Style → Style_ID',
            'Purpose': 'Historical demand analysis'
        }
    ])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table = ax.table(cellText=integration_summary.values,
                     colLabels=integration_summary.columns,
                     cellLoc='left',
                     loc='center',
                     colWidths=[0.25, 0.25, 0.2, 0.3])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Style the header
    for i in range(len(integration_summary.columns)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(integration_summary) + 1):
        for j in range(len(integration_summary.columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
    
    plt.title('Beverly Knits Data Integration Summary', fontsize=16, weight='bold', pad=20)
    plt.savefig('integration_summary_table.png', dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    # Create all visualizations
    print("Creating data relationship diagram...")
    create_data_relationship_diagram()
    
    print("Creating data flow diagram...")
    create_data_flow_diagram()
    
    print("Creating integration summary table...")
    create_integration_summary_table()
    
    print("\nAll visualizations created successfully!")