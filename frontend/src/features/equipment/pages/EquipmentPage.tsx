/**
 * EquipmentPage Component
 *
 * Equipment and work centers management:
 * - Single Responsibility: Equipment tracking
 * - Manage machines, work centers, maintenance
 * - Protected route (requires authentication)
 */

export const EquipmentPage = () => {
  return (
    <div className="equipment-page">
      <h1>Equipment</h1>
      <p>Manage work centers and equipment</p>
      {/* Equipment list and maintenance tracking will go here */}
    </div>
  )
}

EquipmentPage.displayName = 'EquipmentPage'
