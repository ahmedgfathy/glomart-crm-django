# Visual Filter Builder - User Guide 🎯

## ✅ **NO MORE JSON!** Simple Point-and-Click Filter Creation

---

## How to Create "Commercial Properties Only" Filter

### Step 1: Open the Modal
1. Go to **Manage Profiles**
2. Click on **"commercial-employee"** profile
3. Switch to **"Data Filters"** tab
4. Click **"Add Filter"** button

### Step 2: Fill Basic Info
- **Filter Name:** `Commercial Properties Only`
- **Module:** Select "Property"
- **Description:** (Optional) `Shows only commercial properties`
- **Model Name:** `Property`
- **Filter Type:** `Include - Show only matching records`

### Step 3: Use the Visual Builder (NO JSON NEEDED!)

You'll see a section called **"Filter Conditions"** with a visual builder.

#### Option A: For Property Type Name (Recommended)
1. Click **"Add Condition"** (it's already added by default)
2. **Field:** Select "Property Type Name"
3. **Operator:** Select "Contains (text)"
4. **Value:** Type `commercial`

That's it! The system will automatically show only properties where the type name contains "commercial".

#### Option B: For Specific Property Type IDs
If you know the exact IDs of commercial property types:
1. **Field:** Select "Property Type ID"
2. **Operator:** Select "Is one of (comma-separated)"
3. **Value:** Type `1, 3, 5` (the IDs of your commercial types)

### Step 4: Save
1. Toggle **Active** to ON (should be on by default)
2. Click **"Save Filter"**
3. Done! ✅

---

## Common Filter Examples

### 1. Show Only Commercial Properties
**Field:** Property Type Name  
**Operator:** Contains (text)  
**Value:** `commercial`

### 2. Show Properties Above $500,000
**Field:** Price  
**Operator:** Greater than or equal  
**Value:** `500000`

### 3. Show Only Active Properties
**Field:** Is Active  
**Operator:** Equals (boolean/ID)  
**Value:** `true`

### 4. Show Only User's Assigned Properties
**Field:** Assigned To (User ID)  
**Operator:** Equals (boolean/ID)  
**Value:** `{{ user.id }}` (special variable - system auto-fills)

### 5. Multiple Conditions (AND logic)
Click "Add Condition" multiple times:
1. **Property Type Name** contains `commercial`
2. **Status** equals `available`
3. **Price** greater than `100000`

All conditions must match (AND logic).

---

## Available Fields for Properties

| Field | Description | Example Values |
|-------|-------------|----------------|
| **Property Type Name** | The type name | commercial, residential |
| **Property Type ID** | Exact ID number | 1, 2, 3 |
| **Status** | Property status | available, sold, rented |
| **Price** | Property price | 500000 |
| **Area** | Size in sqm/sqft | 1500 |
| **Location** | Address/Location | Downtown, Marina |
| **City** | City name | Dubai, Abu Dhabi |
| **Assigned To (Username)** | Username | john.doe |
| **Assigned To (User ID)** | User ID number | 5 |
| **Created Date** | When created | 2025-01-01 |
| **Is Featured** | Featured flag | true, false |
| **Is Active** | Active flag | true, false |

---

## Available Fields for Leads

| Field | Description |
|-------|-------------|
| **Lead Name** | Full name |
| **Email** | Email address |
| **Phone** | Phone number |
| **Status** | Lead status (new, contacted, etc.) |
| **Source** | Where lead came from |
| **Assigned To (Username)** | Assigned user |
| **Property Type Interest** | What they're looking for |

---

## Operators Explained

| Operator | Use When | Example |
|----------|----------|---------|
| **Contains (text)** | Partial text match | "commercial" finds "Commercial Office" |
| **Equals exactly** | Exact text match | "available" matches only "available" |
| **Is one of** | Match multiple values | "1, 3, 5" matches IDs 1, 3, or 5 |
| **Greater than** | Numbers comparison | Price > 500000 |
| **Greater than or equal** | Numbers comparison | Price >= 500000 |
| **Less than** | Numbers comparison | Price < 1000000 |
| **Less than or equal** | Numbers comparison | Price <= 1000000 |
| **Starts with** | Text starts with | "COM" finds "COM001", "COM002" |
| **Equals (boolean/ID)** | Exact match for IDs or true/false | ID = 5, active = true |

---

## Tips & Tricks

### ✅ Do:
- Use "Contains (text)" for property types (flexible)
- Use "Equals (boolean/ID)" for true/false values
- Use "Is one of" for multiple IDs (comma-separated)
- Add multiple conditions for precise filtering

### ❌ Don't:
- Don't worry about JSON syntax anymore!
- Don't use quotes around numbers
- Don't add spaces in comma-separated IDs (or do, we handle both)

---

## Advanced: JSON Editor (For Experts Only)

If you're comfortable with JSON, you can click **"Advanced: Edit JSON Directly"** at the bottom of the Filter Conditions section.

The visual builder automatically generates the JSON for you, but you can edit it directly if needed.

**Example auto-generated JSON:**
```json
{
  "property_type__name__icontains": "commercial",
  "status": "available",
  "price__gte": 500000
}
```

---

## Testing Your Filter

### After Creating the Filter:

1. **Logout** from admin
2. **Login as** the user with the profile (e.g., "fathy")
3. **Go to** Properties module
4. **Verify:** You should only see filtered properties!

### If Not Working:

**Checklist:**
- ✅ Filter is marked as "Active"
- ✅ Module is set to "Properties"
- ✅ Model Name is exactly "Property" (case-sensitive)
- ✅ At least one condition is added
- ✅ User is assigned to the correct profile
- ✅ User logged out and back in (session refresh)

---

## Need Help?

### Common Issue: "Condition not working"
- Check that the field name matches what's in your database
- For property types, use "Property Type Name" with "Contains" operator
- Values are case-insensitive when using "Contains"

### Common Issue: "No properties showing"
- Make sure you have properties with matching criteria
- Try a simpler condition first (just one field)
- Check the filter is marked as "Active"

---

**Now go create that commercial properties filter - NO JSON NEEDED!** 🚀
