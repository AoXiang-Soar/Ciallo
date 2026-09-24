import os
import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10

# Configure paths
paths = [
    "./data/defects4j_Ciallo_gpt-4o"
]

# Collect all token data for our framework
all_tokens = []
for path in paths:
    for file in os.listdir(path):
        if file.endswith("_summary.csv"):
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Defects4j 2.0
                    if file.startswith('Collections') and 1 <= int(row['bug_id'].strip()) <= 24: continue
                    if row.get('rc') and row['rc'].strip():
                        all_tokens.append(int(row['rc'].strip()))

# Convert to thousands and calculate statistics
if all_tokens:
    ciallo_tokens_k = [t / 1000 for t in all_tokens]
    # Calculate statistics for Ciallo
    ciallo_min = min(ciallo_tokens_k)
    ciallo_q1 = np.percentile(ciallo_tokens_k, 25)
    ciallo_median = np.median(ciallo_tokens_k)
    ciallo_q3 = np.percentile(ciallo_tokens_k, 75)
    ciallo_max = max(ciallo_tokens_k)
    ciallo_actual_max = ciallo_max  # Save actual maximum for annotation
else:
    ciallo_min = ciallo_q1 = ciallo_median = ciallo_q3 = ciallo_max = 0
    ciallo_actual_max = 0

# Boxplot parameters for each framework [min, Q1, median, Q3, max] (unit: thousands)
frameworks_data = {
    "ChatRepair": [19, 180, 282, 350, 420],  # Just as same as the research data of Ye et al.
    "RepairAgent": [21, 110, 170, 220, 315],
    "AdverIntent-Agent": [91, 145, 248, 310, 365],
    "Ciallo": [ciallo_min, ciallo_q1, ciallo_median, ciallo_q3, ciallo_max]
}

# Create a figure with two subplots
fig, axes = plt.subplots(1, 2, figsize=(14, 6))  # Slightly increase width

# Framework order
frameworks = ["ChatRepair", "RepairAgent", "AdverIntent-Agent", "Ciallo"]
colors = ['gray', 'gray', 'gray', 'gray']

# ========== Subplot a: Box Plot ==========
ax_a = axes[0]

# Draw boxplot for each framework
for i, framework in enumerate(frameworks):
    data = frameworks_data[framework]
    min_val, q1, median, q3, max_val = data

    # Draw box
    box_width = 0.5
    box = Rectangle((i + 1 - box_width / 2, q1), box_width, q3 - q1,
                    facecolor=colors[i], edgecolor='black', linewidth=1)
    ax_a.add_patch(box)

    # Draw median line
    ax_a.plot([i + 1 - box_width / 2, i + 1 + box_width / 2], [median, median],
              color='black', linewidth=1.5)

    # Draw whiskers
    # Upper whisker
    ax_a.plot([i + 1, i + 1], [q3, max_val], color='black', linewidth=1)
    ax_a.plot([i + 1 - box_width / 4, i + 1 + box_width / 4], [max_val, max_val],
              color='black', linewidth=1)
    # Lower whisker
    ax_a.plot([i + 1, i + 1], [q1, min_val], color='black', linewidth=1)
    ax_a.plot([i + 1 - box_width / 4, i + 1 + box_width / 4], [min_val, min_val],
              color='black', linewidth=1)

    # Annotate statistics near the boxplot
    # Annotate minimum
    ax_a.text(i + 1, min_val - 8, f'{min_val:.0f}K', ha='center', va='center', fontsize=9)
    # Annotate Q1
    ax_a.text(i + 1 - box_width / 2 - 0.05, q1, f'{q1:.0f}K', ha='center', va='top', fontsize=9)
    # Annotate median
    ax_a.text(i + 1 + box_width / 2 + 0.01, median, f'{median:.0f}K', ha='left', va='center', fontsize=9)
    # Annotate Q3
    ax_a.text(i + 1 - box_width / 2 - 0.05, q3, f'{q3:.0f}K', ha='center', va='bottom', fontsize=9)
    # Annotate maximum (except for Ciallo's special handling)
    if framework != "Ciallo":
        ax_a.text(i + 1, max_val + 8, f'{max_val:.0f}K', ha='center', va='center', fontsize=9)

# Annotate Ciallo's maximum (outside y-axis range)
ciallo_idx = frameworks.index("Ciallo") + 1
ciallo_data = frameworks_data["Ciallo"]

# Add break symbol on the plot
break_y = 475
ax_a.plot([ciallo_idx - 0.2, ciallo_idx + 0.2], [break_y, break_y],
          color='black', linewidth=1.5, linestyle='--')

# Annotate Ciallo's actual maximum
if ciallo_actual_max > 500:
    # Add annotation text box
    annotation_text = f'{ciallo_actual_max:.0f}K'
    ax_a.annotate(annotation_text,
                  xy=(ciallo_idx, break_y),  # Arrow point position
                  xytext=(ciallo_idx, 475),  # Text position
                  ha='center',
                  va='bottom',
                  fontsize=9,
                  color='black')

# Set X-axis labels
ax_a.set_xticks(range(1, len(frameworks) + 1))
ax_a.set_xticklabels(frameworks, fontsize=11)

# Set Y-axis range (limit to 500K)
y_max_limit = 500
y_min = -20
ax_a.set_ylim(y_min, y_max_limit)

# Set Y-axis label format
ax_a.set_ylabel('Token Cost', fontsize=12)
ax_a.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}K'))

# Set subplot a properties
# ax_a.set_title('(a) Token Cost', fontsize=13)
ax_a.set_xlabel('(a) Token Cost', fontsize=13)
ax_a.grid(True, axis='y', alpha=0.3, linestyle='--')

# ========== Subplot b: Median Bar Chart ==========
ax_b = axes[1]

# Extract medians for each framework
medians = [0.03*frameworks_data[framework][2] for framework in frameworks]  # Index 2 corresponds to median

# Create bar chart
bars = ax_b.bar(frameworks, medians, color=colors, edgecolor='black', linewidth=1, width=0.7)

# Annotate values above bars
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax_b.text(bar.get_x() + bar.get_width()/2., height + 0.1,
              f'{height:.2f}¢', ha='center', va='bottom', fontsize=10)
ax_b.set_xticks(range(len(frameworks)))
ax_b.set_xticklabels(frameworks, fontsize=11)

# Set Y-axis
ax_b.set_ylabel('Cost (Cents)', fontsize=12)
ax_b.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}'))

# Set subplot b properties
# ax_b.set_title('(b) Money Cost per Approach (Based on Median Token Cost)', fontsize=13)
ax_b.set_xlabel('(b) Money Cost per Approach (Based on Median Token Cost)', fontsize=13)
ax_b.grid(True, axis='y', alpha=0.3, linestyle='--')
ax_b.set_ylim(0, max(medians) * 1.2)  # Automatically adjust y-axis range, leave 20% space for annotation

# Add note at bottom of figure (if there are outliers)
# if ciallo_actual_max > 500:
#     plt.figtext(0.5, 0.01,
#                 f'Note: Ciallo has an outlier with maximum token cost of {ciallo_actual_max:.0f}K. Boxplot y-axis is limited to 500K for better visualization.',
#                 ha='center', fontsize=10, style='italic', color='black')

# Adjust layout
plt.tight_layout(rect=(0, 0.05, 1, 0.98))  # Reserve space for bottom note
fig.subplots_adjust(left=0.05, right=0.98, bottom=0.1, top=0.9, wspace=0.4)

# Display figure
plt.show()