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
Rect={new=function(...)return {...,_type="Rect"}end}
ColorSequenceKeypoint={new=function(t,c)return {Time=t,Value=c}end}
ColorSequence={new=function(v)return {Keypoints=v,_type="ColorSequence"}end}
NumberSequenceKeypoint={new=function(t,v)return {Time=t,Value=v}end}
NumberSequence={new=function(v)return {Keypoints=v,_type="NumberSequence"}end}
Path2DControlPoint={new=function(p,l,r)return {Position=p,LeftTangent=l,RightTangent=r,_type="Path2DControlPoint"}end}
Enum=setmetatable({},{__index=function(t,k)local e=setmetatable({},{__index=function(_,n)return k.."."..n end});rawset(t,k,e);return e end})
local guiClasses={ScreenGui=true,SurfaceGui=true,BillboardGui=true,Frame=true,CanvasGroup=true,ScrollingFrame=true,TextLabel=true,TextButton=true,TextBox=true,ImageLabel=true,ImageButton=true,UIGradient=true,UICorner=true,UIStroke=true,UIScale=true,UIPadding=true,UIListLayout=true,UIGridLayout=true,UIAspectRatioConstraint=true,UITextSizeConstraint=true,UISizeConstraint=true,ObjectValue=true,LocalScript=true,Path2D=true,UIFlexItem=true,UIDragDetector=true,UIShadow=true,StyleSheet=true}
local I={};I.__index=function(t,k)if k=="AbsoluteSize"then return Vector2.new(400,300)end if k=="AbsolutePosition"then return Vector2.new(0,0)end return I[k]end
local allInstances={};local nextId=0
local function copyValue(v,seen)if type(v)~="table"then return v end seen=seen or {};if seen[v]then return seen[v]end local o={};seen[v]=o;for k,x in pairs(v)do o[copyValue(k,seen)]=copyValue(x,seen)end return setmetatable(o,getmetatable(v))end
local function create(class)
 nextId=nextId+1
 local t=setmetatable({ClassName=class,Name=class,Parent=nil,_children={},_attrs={},_props={},_signals={},_id=nextId},I)
 rawset(t,"ZIndex",1);rawset(t,"Rotation",0);rawset(t,"BackgroundTransparency",0);rawset(t,"TextTransparency",0);rawset(t,"Visible",true)
 if class=="UIGradient"then t.Type=Enum.GradientType.Linear;t.Scale=1;t.TileMode=Enum.GradientTileMode.Clamp;t.Rotation=0;t.Offset=Vector2.new(0,0)end
 if class=="UICorner"then t.CornerRadius=UDim.new(0,8)end
 if class=="UIStroke"then t.Thickness=1;t.Transparency=0 end
 if class=="Path2D"then t._points={}end
 table.insert(allInstances,t);return t
end
Instance={new=create}
function I:IsA(c)return self.ClassName==c or (c=="GuiObject" and (self.ClassName=="Frame" or self.ClassName=="CanvasGroup" or self.ClassName=="ScrollingFrame" or self.ClassName=="TextLabel" or self.ClassName=="TextButton" or self.ClassName=="TextBox" or self.ClassName=="ImageLabel" or self.ClassName=="ImageButton")) or (c=="LayerCollector" and (self.ClassName=="ScreenGui" or self.ClassName=="SurfaceGui" or self.ClassName=="BillboardGui")) or (c=="LuaSourceContainer" and self.ClassName=="LocalScript")end
function I:GetChildren()local o={}for _,c in ipairs(self._children)do table.insert(o,c)end return o end
function I:GetDescendants()local o={}local function walk(n)for _,c in ipairs(n._children)do table.insert(o,c);walk(c)end end walk(self);return o end
function I:FindFirstChild(n)for _,c in ipairs(self._children)do if c.Name==n then return c end end end
function I:FindFirstChildOfClass(c)for _,x in ipairs(self._children)do if x.ClassName==c then return x end end end
function I:FindFirstAncestorOfClass(c)local p=self.Parent;while p do if p.ClassName==c then return p end;p=p.Parent end end
function I:GetFullName()return self.Parent and self.Parent:GetFullName().."."..self.Name or self.Name end
function I:SetAttribute(k,v)self._attrs[k]=v end
function I:GetAttribute(k)return self._attrs[k]end
I.DescendantAdded={Connect=function()end}
function I:GetPropertyChangedSignal(p)self._signals[p]=self._signals[p]or {Connect=function(_,f)self._signals[p].fn=f;return {Disconnect=function()end}end};return self._signals[p]end
function I:Clone()local c=create(self.ClassName);for k,v in pairs(self._props)do c[k]=copyValue(v)end;c.Name=self.Name;c._attrs=copyValue(self._attrs);for _,child in ipairs(self._children)do child:Clone().Parent=c end;return c end
function I:ClearAllChildren()for _,c in ipairs(self:GetChildren())do c:Destroy()end end
function I:Destroy()if self.Parent then for i,c in ipairs(self.Parent._children)do if c==self then table.remove(self.Parent._children,i);break end end;rawset(self,"Parent",nil)end;self._destroyed=true end
function I:SetControlPoints(p)self._points=copyValue(p)end
function I:GetControlPoints()return self._points end
I.__newindex=function(t,k,v)
 if k=="Parent"then local old=rawget(t,"Parent");if old then for i,c in ipairs(old._children)do if c==t then table.remove(old._children,i);break end end end;rawset(t,"Parent",v);if v then table.insert(v._children,t)end;return end
 rawset(t,k,v);t._props[k]=v
 if t._signals[k]and t._signals[k].fn then t._signals[k].fn()end
end
local starter=create("Folder");starter.Name="StarterGui";starter.ClipsDescendantsSupportsRotation=Enum.ClipsDescendantsSupportsRotation.Enabled
local services={StarterGui=starter,ReplicatedStorage=create("Folder"),ReplicatedFirst=create("Folder"),Workspace=create("Folder"),Players=create("Folder"),RunService=create("Folder")}
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
function typeof(v) return type(v)=="table" and v._type or type(v) end
