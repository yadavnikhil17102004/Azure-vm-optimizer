import json
import os

def get_pricing():
    # Use relative path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'data/vms.json')
    
    if not os.path.exists(file_path):
        # Try local data dir
        file_path = os.path.join(os.getcwd(), 'data/vms.json')
        if not os.path.exists(file_path):
            print(f"File {file_path} not found")
            return
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        targets = ['Standard_E4as_v5', 'Standard_E8as_v5', 'Standard_E16as_v5']
        
        print(f"{'VM Name':<20} | {'RAM':<6} | {'Price/hr':<10} | {'Hours for $100'}")
        print("-" * 60)
        
        for name in targets:
            if name in data:
                regions = data[name]
                for reg in regions:
                    if reg['location'] == 'centralindia':
                        price = reg['price']
                        ram = reg['ram']
                        hours = 100 / price if price > 0 else 0
                        print(f"{name:<20} | {ram:<6} | ${price:<9.3f} | {int(hours)} hrs")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    get_pricing()
