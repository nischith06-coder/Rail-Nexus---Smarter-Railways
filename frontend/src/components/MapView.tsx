import { useEffect, useRef } from 'react'
import L from 'leaflet'

type Props={state?:any,states?:any[],full?:boolean}

const ROUTE=[
  [12.9716,77.5946],[13.3392,77.1010],[13.3145,76.2570],[14.4644,75.9218],
  [15.3647,75.1240],[15.4167,75.6290],[15.8497,74.4977],[16.8270,74.6420],
  [18.5204,73.8567],[23.2599,77.4126],[28.6139,77.2090]
] as L.LatLngExpression[]
const STATIONS=['KSR Bengaluru','Tumakuru','Arsikere','Davangere','Hubballi','Gadag','Belagavi','Miraj','Pune','Bhopal','New Delhi']
const stationIndex:Record<string,number>=Object.fromEntries(STATIONS.map((s,i)=>[s,i]))

function congestionStyle(level:number){
  if(level>=3) return {color:'#ff4d5f',fill:'#ff4d5f',label:'SEVERE'}
  if(level>=2) return {color:'#ffb43b',fill:'#ffb43b',label:'HIGH'}
  if(level>=1) return {color:'#36c8ff',fill:'#36c8ff',label:'MODERATE'}
  return {color:'#46df9a',fill:'#46df9a',label:'CLEAR'}
}

export default function MapView({state,states=[],full}:Props) {
  const ref = useRef<HTMLDivElement|null>(null)
  const mapRef = useRef<L.Map|null>(null)
  const markersRef = useRef<Record<string,L.Marker>>({})
  const congestionLayerRef = useRef<L.LayerGroup|null>(null)
  const routeLayerRef = useRef<L.LayerGroup|null>(null)
  const legendRef = useRef<L.Control|null>(null)

  useEffect(()=>{
    if (!ref.current || mapRef.current) return
    const map=L.map(ref.current,{zoomControl:false}).setView([15.5,77.0],6)
    L.control.zoom({position:'bottomright'}).addTo(map)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap contributors',maxZoom:19}).addTo(map)

    const routeLayer=L.layerGroup().addTo(map)
    const congestionLayer=L.layerGroup().addTo(map)
    routeLayerRef.current=routeLayer
    congestionLayerRef.current=congestionLayer

    // Station nodes. The route itself is redrawn as operational sections below.
    ROUTE.forEach((point,i)=>{
      L.circleMarker(point,{radius:5,color:'#9ce8ff',weight:2,fillColor:'#102b3c',fillOpacity:1})
        .bindTooltip(STATIONS[i],{direction:'top',offset:[0,-6]})
        .addTo(routeLayer)
    })

    const legend=L.control({position:'topright'})
    legend.onAdd=()=>{
      const div=L.DomUtil.create('div','map-legend')
      div.innerHTML=`<b>CONGESTION</b><span><i class="lg-clear"></i>Clear</span><span><i class="lg-mod"></i>Moderate</span><span><i class="lg-high"></i>High</span><span><i class="lg-severe"></i>Severe</span>`
      L.DomEvent.disableClickPropagation(div)
      return div
    }
    legend.addTo(map)
    legendRef.current=legend
    mapRef.current=map
    return ()=>{map.remove();mapRef.current=null;markersRef.current={};congestionLayerRef.current=null;routeLayerRef.current=null}
  },[])

  useEffect(()=>{
    const map=mapRef.current
    const congestionLayer=congestionLayerRef.current
    const routeLayer=routeLayerRef.current
    if(!map||!congestionLayer||!routeLayer)return

    congestionLayer.clearLayers()

    // Aggregate live congestion by route section. This makes the dashboard map
    // answer the operational question: WHERE is congestion occurring?
    const sectionLevels:Record<string,number[]>={}
    ;(states||[]).forEach((t:any)=>{
      const a=stationIndex[t.current_station], b=stationIndex[t.next_station]
      if(a===undefined || b===undefined || b!==a+1)return
      const key=`${a}-${b}`
      const level=Math.max(Number(t.congestion_level||0),Number(t.track_congestion||0))
      ;(sectionLevels[key]??=[]).push(level)
    })

    for(let i=0;i<ROUTE.length-1;i++){
      const values=sectionLevels[`${i}-${i+1}`]||[]
      const selectedHere=state && stationIndex[state.current_station]===i && stationIndex[state.next_station]===i+1
      const selectedLevel=selectedHere ? Math.max(Number(state.congestion_level||0),Number(state.track_congestion||0)) : 0
      const avg=values.length ? values.reduce((a,b)=>a+b,0)/values.length : 0
      const max=values.length ? Math.max(...values) : 0
      const level=Math.max(selectedLevel, max>=3?3:max>=2?2:avg>=1?1:0)
      const style=congestionStyle(level)
      const segment=L.polyline([ROUTE[i],ROUTE[i+1]],{
        color:style.color,weight:level>=2?9:level===1?7:4,opacity:level>=2?.9:.7
      })
      const trainCount=values.length
      segment.bindTooltip(`${STATIONS[i]} → ${STATIONS[i+1]} · ${style.label} congestion${trainCount?` · ${trainCount} live trains`:''}`,{sticky:true})
      segment.addTo(congestionLayer)

      if(level>=2){
        const lat1=Number(ROUTE[i][0]), lat2=Number(ROUTE[i+1][0]), lon1=Number(ROUTE[i][1]), lon2=Number(ROUTE[i+1][1])
        const mid=[(lat1+lat2)/2,(lon1+lon2)/2] as L.LatLngExpression
        L.circleMarker(mid,{radius:level===3?10:8,color:style.color,fillColor:style.fill,fillOpacity:.25,weight:2})
          .bindPopup(`<b>${style.label} CONGESTION</b><br>${STATIONS[i]} → ${STATIONS[i+1]}<br>${trainCount} live trains in this section`) .addTo(congestionLayer)
      }
    }

    // Network-wide hotspots from the full 2,000-train feed. Grid aggregation keeps
    // the map readable while preserving where congestion is actually being reported.
    const buckets:Record<string,{lat:number,lon:number,count:number,max:number}>={}
    ;(states||[]).forEach((t:any)=>{
      const level=Math.max(Number(t.congestion_level||0),Number(t.track_congestion||0))
      if(level<2 || t.latitude==null || t.longitude==null)return
      const lat=Math.round(Number(t.latitude)*4)/4, lon=Math.round(Number(t.longitude)*4)/4
      const key=`${lat}|${lon}`
      const b=buckets[key]??{lat,lon,count:0,max:0}
      b.count++;b.max=Math.max(b.max,level);buckets[key]=b
    })
    Object.values(buckets).slice(0,100).forEach(b=>{
      const st=congestionStyle(b.max)
      L.circle([b.lat,b.lon],{radius:9000,color:st.color,fillColor:st.fill,fillOpacity:.13,weight:2})
        .bindTooltip(`Congestion hotspot · ${b.count} trains · ${st.label}`,{sticky:true})
        .addTo(congestionLayer)
    })

    const allFleet=states.length?states:(state?[state]:[])
    const fleet=allFleet.length>300 ? allFleet.filter((t:any,i:number)=>String(t.train_number)==="12627" || i%7===0).slice(0,300) : allFleet
    const seen=new Set<string>()
    fleet.forEach((t:any)=>{
      if(t?.latitude==null||t?.longitude==null)return
      const n=String(t.train_number);seen.add(n)
      const isSelected=state && String(state.train_number)===n
      const icon=L.divIcon({className:isSelected?'train-marker selected-train-marker':'train-marker',html:`<div class="train-glyph">🚆</div><span>${n}</span>`,iconSize:[58,32],iconAnchor:[15,15]})
      const marker=markersRef.current[n]
      const tip=`${n} · ${t.current_speed ?? '—'} km/h · +${t.current_delay ?? 0} min · congestion ${Math.max(Number(t.congestion_level||0),Number(t.track_congestion||0))}`
      if(marker){marker.setLatLng([t.latitude,t.longitude]);marker.setIcon(icon);marker.bindTooltip(tip)}
      else markersRef.current[n]=L.marker([t.latitude,t.longitude],{icon,zIndexOffset:isSelected?1000:0}).bindTooltip(tip).addTo(map)
    })
    Object.keys(markersRef.current).forEach(n=>{if(!seen.has(n)){markersRef.current[n].remove();delete markersRef.current[n]}})
  },[state,states])

  return <div className={`map-wrap ${full?'map-full':''}`}>
    <div ref={ref} className="map"/>
    <div className="map-operational-label"><span className="pulse-dot"/> LIVE CONGESTION LAYER · RED = SEVERE · AMBER = HIGH</div>
  </div>
}
