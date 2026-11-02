-- Offline GUI double. Tests engine construction/math, NOT Roblox's renderer.
function math.clamp(v,a,b) if v<a then return a elseif v>b then return b end return v end
function math.atan2(y,x) return math.atan(y,x) end
local Vec={};Vec.__index=function(v,k) if k=="Magnitude" then return math.sqrt(v.X^2+v.Y^2) end return Vec[k] end
Vector2={new=function(x,y) return setmetatable({X=x or 0,Y=y or 0,_type="Vector2"},Vec) end}
Vec.__add=function(a,b)return Vector2.new(a.X+b.X,a.Y+b.Y)end
Vec.__mul=function(a,b)if type(a)=="number"then a,b=b,a end return Vector2.new(a.X*b,a.Y*b)end
local U={};U.__index=U
UDim={new=function(s,o)return setmetatable({Scale=s or 0,Offset=o or 0,_type="UDim"},U)end}
local U2={};U2.__index=function(v,k)if k=="Width"then return v.X end if k=="Height"then return v.Y end return U2[k]end
UDim2={new=function(xs,xo,ys,yo)return setmetatable({X=UDim.new(xs,xo),Y=UDim.new(ys,yo),_type="UDim2"},U2)end}
UDim2.fromScale=function(x,y)return UDim2.new(x,0,y,0)end
UDim2.fromOffset=function(x,y)return UDim2.new(0,x,0,y)end
U2.__add=function(a,b)return UDim2.new(a.X.Scale+b.X.Scale,a.X.Offset+b.X.Offset,a.Y.Scale+b.Y.Scale,a.Y.Offset+b.Y.Offset)end
local C={};C.__index=C
Color3={new=function(r,g,b)return setmetatable({R=r or 0,G=g or 0,B=b or 0,_type="Color3"},C)end}
Color3.fromRGB=function(r,g,b)return Color3.new((r or 0)/255,(g or 0)/255,(b or 0)/255)end
function C:ToHex()return string.format("%02X%02X%02X",math.floor(self.R*255+.5),math.floor(self.G*255+.5),math.floor(self.B*255+.5))end
function C:ToHSV()local mx,mn=math.max(self.R,self.G,self.B),math.min(self.R,self.G,self.B);return 0,mx==0 and 0 or (mx-mn)/mx,mx end
Color3.fromHSV=function(h,s,v)return Color3.new(v,v,v)end
function C:Lerp(b,t)return Color3.new(self.R+(b.R-self.R)*t,self.G+(b.G-self.G)*t,self.B+(b.B-self.B)*t)end
Font={new=function(f,w)return {_type="Font",Family=f,Weight=w}end}
Rect={new=function(a,b,c,d)
 if typeof(a)=="Vector2" then return {Min=a,Max=b,_type="Rect"} end
 return {Min=Vector2.new(a,b),Max=Vector2.new(c,d),_type="Rect"}
end}
ColorSequenceKeypoint={new=function(t,c)return {Time=t,Value=c}end}
ColorSequence={new=function(v)return {Keypoints=v,_type="ColorSequence"}end}
NumberSequenceKeypoint={new=function(t,v)return {Time=t,Value=v}end}
NumberSequence={new=function(v)return {Keypoints=v,_type="NumberSequence"}end}
Path2DControlPoint={new=function(p,l,r)return {Position=p or UDim2.fromScale(0,0),LeftTangent=l or UDim2.fromScale(0,0),RightTangent=r or UDim2.fromScale(0,0),_type="Path2DControlPoint"}end}
Enum=setmetatable({},{__index=function(t,k)local e=setmetatable({},{__index=function(_,n)return k.."."..n end});rawset(t,k,e);return e end})
local guiClasses={NumberValue=true,Folder=true,ScreenGui=true,SurfaceGui=true,BillboardGui=true,Frame=true,CanvasGroup=true,ScrollingFrame=true,TextLabel=true,TextButton=true,TextBox=true,ImageLabel=true,ImageButton=true,UIGradient=true,UICorner=true,UIStroke=true,UIScale=true,UIPadding=true,UIListLayout=true,UIGridLayout=true,UIAspectRatioConstraint=true,UITextSizeConstraint=true,UISizeConstraint=true,ObjectValue=true,LocalScript=true,Path2D=true,UIFlexItem=true,UIDragDetector=true,UIShadow=true,StyleSheet=true}
local I={};I.__index=function(t,k)if k=="AbsoluteSize"then return Vector2.new(400,300)end if k=="AbsolutePosition"then return Vector2.new(0,0)end return I[k]end
local allInstances={};local nextId=0
local function copyValue(v,seen)if type(v)~="table"then return v end seen=seen or {};if seen[v]then return seen[v]end local o={};seen[v]=o;for k,x in pairs(v)do o[copyValue(k,seen)]=copyValue(x,seen)end return setmetatable(o,getmetatable(v))end
local function makeSignal()
 local s={_fns={}}
 function s:Connect(f) table.insert(self._fns,f); local alive=true; return {Disconnect=function() if not alive then return end; alive=false; for i,x in ipairs(s._fns) do if x==f then table.remove(s._fns,i); break end end end} end
 function s:Fire(...) for _,f in ipairs(self._fns) do f(...) end end
 return s
end

local function create(class)
 nextId=nextId+1
 local t=setmetatable({ClassName=class,Name=class,Parent=nil,_children={},_attrs={},_props={},_signals={},_id=nextId},I)
 rawset(t,"ZIndex",1);rawset(t,"Rotation",0);rawset(t,"BackgroundTransparency",0);rawset(t,"TextTransparency",0);rawset(t,"Visible",true)
 t.ChildAdded=makeSignal();t.ChildRemoved=makeSignal();t.DescendantAdded=makeSignal();t.DescendantRemoving=makeSignal();t.Destroying=makeSignal();t.AncestryChanged=makeSignal()
 if class=="Path2D"then t.ControlPointChanged=makeSignal()end
 if class=="UIGradient"then t.Type=Enum.GradientType.Linear;t.Scale=1;t.TileMode=Enum.GradientTileMode.Clamp;t.Rotation=0;t.Offset=Vector2.new(0,0)end
 if class=="UICorner"then t.CornerRadius=UDim.new(0,8)end
 if class=="UIStroke"then t.Thickness=1;t.Transparency=0 end
 if class=="Path2D"then t._points={};t.Closed=false;t.Thickness=1;t.Color3=Color3.new()end
 if class=="NumberValue"then t.Value=0;t.Changed=makeSignal()end
 if class=="ObjectValue"then t.Value=nil end
 table.insert(allInstances,t);return t
end
Instance={new=create}
function I:IsA(c)return self.ClassName==c or (c=="GuiObject" and (self.ClassName=="Frame" or self.ClassName=="CanvasGroup" or self.ClassName=="ScrollingFrame" or self.ClassName=="TextLabel" or self.ClassName=="TextButton" or self.ClassName=="TextBox" or self.ClassName=="ImageLabel" or self.ClassName=="ImageButton")) or (c=="LayerCollector" and (self.ClassName=="ScreenGui" or self.ClassName=="SurfaceGui" or self.ClassName=="BillboardGui")) or (c=="LuaSourceContainer" and self.ClassName=="LocalScript")end
function I:GetChildren()local o={}for _,c in ipairs(self._children)do table.insert(o,c)end return o end
function I:GetDescendants()local o={}local function walk(n)for _,c in ipairs(n._children)do table.insert(o,c);walk(c)end end walk(self);return o end
function I:FindFirstChild(n)for _,c in ipairs(self._children)do if c.Name==n then return c end end end
function I:FindFirstChildOfClass(c)for _,x in ipairs(self._children)do if x.ClassName==c then return x end end end
function I:FindFirstAncestorOfClass(c)local p=self.Parent;while p do if p.ClassName==c then return p end;p=p.Parent end end
function I:IsDescendantOf(a)local p=self.Parent;while p do if p==a then return true end;p=p.Parent end;return false end
function I:FindFirstChildWhichIsA(c)for _,x in ipairs(self._children)do if x:IsA(c)then return x end end end
function I:GetFullName()return self.Parent and self.Parent:GetFullName().."."..self.Name or self.Name end
function I:SetAttribute(k,v)local old=self._attrs[k];self._attrs[k]=v;if old~=v and self._attrSignals and self._attrSignals[k]then self._attrSignals[k]:Fire(k) end end
function I:GetAttribute(k)return self._attrs[k]end
-- per-instance lifecycle signals are created in create()
function I:GetPropertyChangedSignal(p)self._signals[p]=self._signals[p]or makeSignal();return self._signals[p]end
function I:GetAttributeChangedSignal(k)self._attrSignals=self._attrSignals or {};self._attrSignals[k]=self._attrSignals[k]or makeSignal();return self._attrSignals[k]end
function I:Clone()local c=create(self.ClassName);for k,v in pairs(self._props)do c[k]=copyValue(v)end;c.Name=self.Name;c._attrs=copyValue(self._attrs);for _,child in ipairs(self._children)do child:Clone().Parent=c end;return c end
function I:ClearAllChildren()for _,c in ipairs(self:GetChildren())do c:Destroy()end end
function I:Destroy()self.Destroying:Fire();if self.Parent then for i,c in ipairs(self.Parent._children)do if c==self then table.remove(self.Parent._children,i);break end end;local old=self.Parent;rawset(self,"Parent",nil);old.ChildRemoved:Fire(self)end;self._destroyed=true end
local function pathPolyline(self)
 local pts=self._points; local n=#pts; if n<2 then return {},0 end
 local segs=self.Closed and n or n-1; local steps=16; local line={}; local len=0; local cum={0}
 local host=self.Parent; local size=host and host.AbsoluteSize or Vector2.new(400,300); local aspect=size.Y>0 and size.X/size.Y or 1
 local function val(u) return u.X.Scale,u.Y.Scale,u.X.Offset,u.Y.Offset end
 for s=1,segs do
  local a,b=pts[s],pts[s%n+1]
  local ax,ay,axo,ayo=val(a.Position); local bx,by,bxo,byo=val(b.Position)
  local arx,ary,arxo,aryo=val(a.RightTangent); local blx,bly,blxo,blyo=val(b.LeftTangent)
  local p0={x=ax,y=ay,xo=axo,yo=ayo}; local p1={x=ax+arx,y=ay+ary,xo=axo+arxo,yo=ayo+aryo}
  local p2={x=bx+blx,y=by+bly,xo=bxo+blxo,yo=byo+blyo}; local p3={x=bx,y=by,xo=bxo,yo=byo}
  for k=0,steps do
   if not (s>1 and k==0) then
    local t=k/steps; local u=1-t; local A,B,C,D=u*u*u,3*u*u*t,3*u*t*t,t*t*t
    local p={x=A*p0.x+B*p1.x+C*p2.x+D*p3.x,y=A*p0.y+B*p1.y+C*p2.y+D*p3.y,xo=A*p0.xo+B*p1.xo+C*p2.xo+D*p3.xo,yo=A*p0.yo+B*p1.yo+C*p2.yo+D*p3.yo}
    if #line>0 then local q=line[#line]; len=len+math.sqrt(((p.x-q.x)*aspect+(p.xo-q.xo)/math.max(1,size.X))^2+((p.y-q.y)+(p.yo-q.yo)/math.max(1,size.Y))^2); cum[#cum+1]=len end
    line[#line+1]=p
   end
  end
 end
 return line,len,cum,aspect,size
end
function I:SetControlPoints(p)self._points=copyValue(p);self._pathCache=nil;if self.ControlPointChanged then self.ControlPointChanged:Fire() end end
function I:GetControlPoints()return self._points end
function I:GetControlPoint(i)return assert(self._points[i],"index out of range") end
function I:InsertControlPoint(i,p)table.insert(self._points,i,copyValue(p));self._pathCache=nil;self.ControlPointChanged:Fire() end
function I:UpdateControlPoint(i,p)self._points[i]=copyValue(p);self._pathCache=nil;self.ControlPointChanged:Fire() end
function I:RemoveControlPoint(i)table.remove(self._points,i);self._pathCache=nil;self.ControlPointChanged:Fire() end
function I:GetMaxControlPoints()return 100 end
function I:GetLength()local _,len=pathPolyline(self);return len end
function I:GetBoundingRect()
 local minx,miny,maxx,maxy=math.huge,math.huge,-math.huge,-math.huge
 for _,p in ipairs(self._points)do minx=math.min(minx,p.Position.X.Scale);maxx=math.max(maxx,p.Position.X.Scale);miny=math.min(miny,p.Position.Y.Scale);maxy=math.max(maxy,p.Position.Y.Scale)end
 local pad=(self.Thickness or 0)/200
 return Rect.new(Vector2.new(minx-pad,miny-pad),Vector2.new(maxx+pad,maxy+pad))
end
function I:GetPositionOnCurve(t)
 local line,len,cum,aspect,size=pathPolyline(self); if #line<2 then error("less than two control points") end
 -- parameter space: distribute t by segment index, not arc length
 local segCount=self.Closed and #self._points or #self._points-1
 local idx=math.clamp(t,0,1)*segCount; local si=math.min(segCount,math.floor(idx)+1); local f=idx-math.floor(idx)
 local steps=16; local base=(si-1)*steps+1; local a,b=line[base+math.floor(f*steps)],line[base+math.min(steps,math.floor(f*steps)+1)]
 local ff=f*steps-math.floor(f*steps)
 return UDim2.new(a.x+(b.x-a.x)*ff,a.xo+(b.xo-a.xo)*ff,a.y+(b.y-a.y)*ff,a.yo+(b.yo-a.yo)*ff)
end
function I:GetPositionOnCurveArcLength(t)
 local line,len,cum,aspect,size=pathPolyline(self); if #line<2 then error("less than two control points") end
 local target=math.clamp(t,0,1)*len; local i=2; while i<#cum and cum[i]<target do i=i+1 end
 local a,b=line[i-1],line[i]; local span=cum[i]-cum[i-1]; local f=span>1e-9 and (target-cum[i-1])/span or 0
 return UDim2.new(a.x+(b.x-a.x)*f,a.xo+(b.xo-a.xo)*f,a.y+(b.y-a.y)*f,a.yo+(b.yo-a.yo)*f)
end
function I:GetTangentOnCurve(t)local p=self:GetPositionOnCurve(math.max(0,t-0.001));local q=self:GetPositionOnCurve(math.min(1,t+0.001));local v=Vector2.new(q.X.Scale-p.X.Scale,q.Y.Scale-p.Y.Scale);local m=v.Magnitude;if m<1e-9 then return Vector2.new(1,0)end return Vector2.new(v.X/m,v.Y/m)end
function I:GetTangentOnCurveArcLength(t)local p=self:GetPositionOnCurveArcLength(math.max(0,t-0.001));local q=self:GetPositionOnCurveArcLength(math.min(1,t+0.001));local v=Vector2.new(q.X.Scale-p.X.Scale,q.Y.Scale-p.Y.Scale);local m=v.Magnitude;if m<1e-9 then return Vector2.new(1,0)end return Vector2.new(v.X/m,v.Y/m)end
I.__newindex=function(t,k,v)
 if k=="Parent"then local old=rawget(t,"Parent");if old then for i,c in ipairs(old._children)do if c==t then table.remove(old._children,i);break end end;old.ChildRemoved:Fire(t)end;rawset(t,"Parent",v);if v then table.insert(v._children,t);v.ChildAdded:Fire(t);local a=v;while a do a.DescendantAdded:Fire(t);a=a.Parent end end;return end
 if k=="Value"and t.ClassName=="NumberValue"then rawset(t,k,v);t._props[k]=v;t.Changed:Fire(v);return end
 rawset(t,k,v);t._props[k]=v
 if t._signals[k]then t._signals[k]:Fire()end
end
local function jsonEncode(v)
 local ty=type(v)
 if ty=="nil"then return "null" elseif ty=="boolean"then return tostring(v) elseif ty=="number"then return tostring(v)
 elseif ty=="string"then return '"'..v:gsub('\\','\\\\'):gsub('"','\\"'):gsub('\n','\\n'):gsub('\r','\\r'):gsub('\t','\\t')..'"'
 elseif ty=="table"then
  local n=#v; local isArr=n>0 or next(v)==nil
  if isArr then local parts={};for i=1,n do parts[#parts+1]=jsonEncode(v[i])end;return "["..table.concat(parts,",").."]"
  else local parts={};for k,x in pairs(v)do parts[#parts+1]=jsonEncode(tostring(k))..":"..jsonEncode(x)end;return "{"..table.concat(parts,",").."}" end
 else error("cannot encode "..ty) end
end
local function jsonDecode(str)
 local pos=1
 local function skip()while pos<=#str and str:sub(pos,pos):match("%s")do pos=pos+1 end end
 local parse
 local function parseString()
  pos=pos+1;local out={}
  while pos<=#str do local c=str:sub(pos,pos);pos=pos+1
   if c=='"'then return table.concat(out) elseif c=="\\"then local e=str:sub(pos,pos);pos=pos+1;out[#out+1]=({n="\n",r="\r",t="\t",['"']='"',["\\"]="\\",["/"]="/"})[e] or e
   else out[#out+1]=c end
  end error("unterminated string")
 end
 parse=function()
  skip();local c=str:sub(pos,pos)
  if c=='"'then return parseString() elseif c=="{"then pos=pos+1;local o={};skip();if str:sub(pos,pos)=="}"then pos=pos+1;return o end
   while true do skip();local k=parseString();skip();assert(str:sub(pos,pos)==":");pos=pos+1;o[k]=parse();skip();local d=str:sub(pos,pos);pos=pos+1;if d=="}"then return o end;assert(d==",")end
  elseif c=="["then pos=pos+1;local a={};skip();if str:sub(pos,pos)=="]"then pos=pos+1;return a end
   while true do a[#a+1]=parse();skip();local d=str:sub(pos,pos);pos=pos+1;if d=="]"then return a end;assert(d==",")end
  elseif str:sub(pos,pos+3)=="true"then pos=pos+4;return true elseif str:sub(pos,pos+4)=="false"then pos=pos+5;return false
  elseif str:sub(pos,pos+3)=="null"then pos=pos+4;return nil
  else local n=str:match("^-?%d+%.?%d*[eE]?[+-]?%d*",pos);assert(n,"bad json at "..pos);pos=pos+#n;return tonumber(n) end
 end
 return parse()
end
local heartbeat=makeSignal()
local starter=create("Folder");starter.Name="StarterGui";starter.ClipsDescendantsSupportsRotation=Enum.ClipsDescendantsSupportsRotation.Enabled
local runService=create("Folder");runService.Heartbeat=heartbeat
local services={StarterGui=starter,ReplicatedStorage=create("Folder"),ReplicatedFirst=create("Folder"),Workspace=create("Folder"),Players=create("Folder"),RunService=runService,HttpService={JSONEncode=function(_,v)return jsonEncode(v)end,JSONDecode=function(_,v)return jsonDecode(v)end},TweenService=create("Folder")}
game={GetService=function(_,n)return services[n]end}
services.StarterGui.Name="StarterGui";services.ReplicatedStorage.Name="ReplicatedStorage";services.ReplicatedFirst.Name="ReplicatedFirst";services.Workspace.Name="Workspace"
task={defer=function(f)f()end,spawn=function(f)f()end,wait=function()end}
local refs={};local id=0
function describeRef(i)id=id+1;local r="#"..id;refs[r]=i;return {id=r,name=i.Name,className=i.ClassName,path=i:GetFullName()}end
function resolveRef(r)return refs[r] or (r=="game.StarterGui" and starter) or nil,"not found" end
function ok(t)return {ok=true,result=t}end
function failCode(c,m)return {ok=false,code=c,error=m}end
function waypoint()end
tools={}
function fireHeartbeat(dt)heartbeat:Fire(dt or 1/30)end
function typeof(v) return type(v)=="table" and v._type or type(v) end
