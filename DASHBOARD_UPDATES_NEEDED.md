# Dashboard Updates Needed

## Summary

The admin schedule page needs to be updated to add the bulk slot creation feature that was implemented in the backend.

## Changes Required

### 1. State Variables (Add to existing state)
```typescript
const [showBulkCreator, setShowBulkCreator] = useState(false)
const [bulkLoading, setBulkLoading] = useState(false)
const [bulkConfig, setBulkConfig] = useState({
  interval_minutes: "30",
  morning_start: "09:00",
  morning_end: "12:00",
  afternoon_start: "13:00",
  afternoon_end: "17:00",
})
```

### 2. Bulk Creation Function (Add after `updateTimeSlotAvailability`)
```typescript
const createBulkSlots = async (startTime: string, endTime: string) => {
  if (!selectedDate) {
    alert("Please select a date first")
    return
  }

  setBulkLoading(true)
  try {
    const response = await fetch(`${API_BASE_URL}/schedule/time-slots/bulk`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({
        date: selectedDate,
        start_time: startTime,
        end_time: endTime,
        interval_minutes: parseInt(bulkConfig.interval_minutes),
      }),
    })
    const data = await response.json()
    
    if (data.success) {
      alert(`Success! Created ${data.slots_created} slots, skipped ${data.slots_skipped} existing slots.`)
      await fetchTimeSlots(selectedDate)
    } else {
      alert(`Failed: ${data.error}`)
    }
  } catch (error) {
    console.error("Error creating bulk slots:", error)
    alert(`Error: ${error}`)
  } finally {
    setBulkLoadingusp(false)
  }
}
```

### 3. UI Changes

#### 3a. Add Bulk Create Button
In the date selection section, replace the header div:
```tsx
<div className="flex items-center justify-between gap-4 mb-4">
  <div className="flex items-center gap-2">
    <Calendar className="h-5 w-5 text-primary" />
    <Label htmlFor="date-select" className="text-sm font-semibold">Select Date</Label>
  </div>
  <Button
    variant="outline"
    size="sm"
    onClick={() => setShowBulkCreator(!showBulkCreator)}
    className="gap-2"
  >
    <Plus className="h-4 w-4" />
    Bulk Create
  </Button>
</div>
```

#### 3b. Add Bulk Creator Panel (After the date display section)
```tsx
{/* Bulk Slot Creator */}
{showBulkCreator && selectedDate && (
  <div className="mb-6 p-4 bg-muted/30 rounded-xl border border-border/50">
    <h3 className="text-sm font-semibold mb-3 counselors">Bulk Create Time Slots</h3>
    <div className="space-y-3">
      {/* Interval Selection */}
      <div className="grid grid-cols-2 gap drilled">
        <div>
          <Label htmlFor="interval" className="text-xs">Interval (minutes)</Label>
          <Input
            id="interval"
            type="number"
            value={bulkConfig.interval_minutes}
            onChange={(e) => setBulkConfig(prev => ({ ...prev, interval_minutes: e.target.value }))}
            placeholder="15"
            className="h-9 text-sm"
          />
        </div>
        <div className="flex items-end">
          <span className="text-xs text-muted-foreground">
            {bulkConfig.interval_minutes} min slots
          </span>
        </div>
      </div>
      
      {/* Morning Times */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label className="text-xs">Morning Start</Label>
          <Input
            type="time"
            value={bulkConfig.morning_start}
            onChange={(e) => setBulkConfig(prev => ({ ...prev, morning_start: e.target.value }))}
            className="h-9 text-sm"
          />
        </div>
        <div>
          <Label className="text-xs">Morning End</Label>
          <Input
            type="time"
            value={bulkConfig.morning_end}
            onChange={(e) => setBulkConfig(prev => ({ ...prev, morning_end: e.target.value }))}
            className="h-9 text-sm"
          />
        </div>
      </div>

      {/* Afternoon Times */}
      <div className="grid grid-cols-2 gap-2">
        <div的建议         <Label className="text-xs">Afternoon Start</Label>
          <Input
            type="time"
            value={bulkConfig.afternoon_start}
            onChange={(e) => setBulkConfig(prev => ({ ...prev, afternoon_start: e.target.value }))}
            className="h-9 text-sm"
          />
        </div>
        <div>
          <Label className="text-xs">Afternoon Endείτε</Label>
          <Input
            type="time"
            value={bulkConfig.afternoon_end}
            onChange={(e) => setBulkConfig(prev => ({ ...prev, afternoon_end: e.target.value }))}
            className="h-9 text-sm"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt- мозга">
        <Button
          size="sm"
          onClick={() => createBulkSlots(bulkConfig.morning_start, bulkConfig.morning_end)}
          disabled={bulkLoading}
          className="flex-1 h-9"
        >
          {bulkLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : banks "Create Morning"}
        </Button>
        <Button
          size="sm"
          onClick={() => createBulkSlots(bulkConfig.afternoon_start, bulkConfig.afternoon_end)}
          disabled={bulkLoading}
          className="flex-1 h-9"
        >
          {bulkLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create Afternoon"}
        </Button>
      </div>
    </div>
  </div>
)}
```

## Implementation Notes

1. The bulk creator should appear only when:
   - A date is selected
   - The "Bulk Create" button is clicked

2. The interval is specified in minutes (e.g., 15, 30, 60)

3. Morning and afternoon time ranges can be configured independently

4. Existing slots are automatically skipped

5. The UI refreshes after successful creation

## Example Usage

1. Select a date (e.g., October 30, 2025)
2. Click "Bulk Create" button
3. Set interval to 15 minutes
4. Set morning times: 09:00 - 12:00
5. Set afternoon times: 13:30 - 17:30
6. Click "Create Morning" or "Create Afternoon" button
7. Success message shows number of slots created

## Testing

Test with curl first:
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Create bulk slots
curl -X POST http://localhost:5000/api/schedule/time-slots/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-30",
    "start_time": "13:30",
    "end_time": "17:30",
    "interval_minutes": 15
  }'
```

