import os

routes_file = 'ocs-portal-py/user_building_routes.py'
with open(routes_file, 'r') as f:
    content = f.read()
    
checks = [
    ('@app.get("/users/edit/{user_id}")', 'GET Edit User Route'),
    ('@app.post("/users/edit/{user_id}")', 'POST Edit User Route'), 
    ('@app.post("/users/delete/{user_id}")', 'POST Delete User Route'),
    ('def edit_user_form(', 'Edit User Form Function'),
    ('def edit_user_submit(', 'Edit User Submit Function'),
    ('def delete_user_submit(', 'Delete User Submit Function')
]

print('Edit User Route Verification:')
print('=' * 50)
all_found = True
for check, name in checks:
    if check in content:
        print(f'✅ {name} - Found')
    else:
        print(f'❌ {name} - Missing')
        all_found = False

print('=' * 50)
if all_found:
    print('🎉 All Edit User routes are properly implemented!')
    print('✅ The Edit User functionality should now work correctly.')
else:
    print('❌ Some routes are missing.')
