from metaflow import FlowSpec, step
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class ShowcaseFlow(FlowSpec):

    @step
    def start(self):
        self.df = pd.DataFrame({
            'Category': ['Fruit', 'Fruit', 'Fruit', 'Vegetable', 'Vegetable'],
            'Item': ['Apple', 'Banana', 'Cherry', 'Carrot', 'Broccoli'],
            'Score': np.random.randint(50, 100, 5)
        })
        self.metadata = {"version": "2.0", "env": "dev"}
        self.matrix = np.eye(3)
        self.items = [10, 20, 30, 40, 50]
        
        self.categories = ['Fruit', 'Vegetable']
        self.next(self.per_category, foreach='categories')

    @step
    def per_category(self):
        self.category = self.input
        self.sub_items = self.df[self.df['Category'] == self.category]['Item'].tolist()
        self.next(self.per_item, foreach='sub_items')

    @step
    def per_item(self):
        self.item = self.input
        self.result_value = len(self.item) * 10
        self.next(self.join_items)

    @step
    def join_items(self, inputs):
        self.merge_artifacts(inputs, exclude=['item', 'result_value'])
        self.category_results = {inp.item: inp.result_value for inp in inputs}
        self.category = inputs[0].category
        self.next(self.join_categories)

    @step
    def join_categories(self, inputs):
        self.merge_artifacts(inputs, exclude=['category_results', 'category', 'sub_items'])
        self.full_results = {}
        for inp in inputs:
            self.full_results.update(inp.category_results)
        self.next(self.end)

    @step
    def end(self):
        fig, ax1 = plt.subplots(1, 1, figsize=(8, 5))
        fig.patch.set_facecolor('#ffffff')

        items = list(self.full_results.keys())
        values = list(self.full_results.values())
        colors = ['#6C5CE7' if x > 60 else '#A29BFE' for x in values]
        
        ax1.bar(items, values, color=colors)
        ax1.set_title("Processed Item Metrics", fontsize=14, pad=15, fontweight='bold')
        ax1.set_ylabel("Calculated Value")
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()
        
        self.dashboard = fig
        
        print("ShowcaseFlow finished successfully!")
        print(f"Final Data: {self.full_results}")

if __name__ == '__main__':
    ShowcaseFlow()
