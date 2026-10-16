-- Offline Roblox double: verifies planning, transforms, limits and cleanup.
-- It does NOT claim to simulate Roblox's geometry/CSG kernel.
local V = {}; V.__index = function(v,k)
    if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
    if k=="Unit" then return v/v.Magnitude end
    return V[k]
end
Vector3 = {new=function(x,y,z) return setmetatable({X=x or 0,Y=y or 0,Z=z or 0,_type="Vector3"},V) end}
V.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
V.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
V.__unm=function(a) return Vector3.new(-a.X,-a.Y,-a.Z) end
V.__mul=function(a,b) if type(a)=="number" then a,b=b,a end; return Vector3.new(a.X*b,a.Y*b,a.Z*b) end
V.__div=function(a,b) return a*(1/b) end
function V:Dot(b) return self.X*b.X+self.Y*b.Y+self.Z*b.Z end
function V:Cross(b) return Vector3.new(self.Y*b.Z-self.Z*b.Y,self.Z*b.X-self.X*b.Z,self.X*b.Y-self.Y*b.X) end
Vector3.zero=Vector3.new(); Vector3.one=Vector3.new(1,1,1)
Vector3.xAxis=Vector3.new(1,0,0);Vector3.yAxis=Vector3.new(0,1,0);Vector3.zAxis=Vector3.new(0,0,1)
local CF={};CF.__index=CF
CFrame={}
function CFrame.fromMatrix(p,x,y,z) return setmetatable({Position=p,x=x,y=y,z=z,_type="CFrame"},CF) end
function CFrame.new(x,y,z)
    local p=type(x)=="table" and x or Vector3.new(x,y,z)
    return CFrame.fromMatrix(p,Vector3.xAxis,Vector3.yAxis,Vector3.zAxis)
end
function CF:vector(v) return self.x*v.X+self.y*v.Y+self.z*v.Z end
CF.__mul=function(a,b)
    if b._type=="Vector3" then return a.Position+a:vector(b) end
    return CFrame.fromMatrix(a*b.Position,a:vector(b.x),a:vector(b.y),a:vector(b.z))
end
CF.__add=function(a,b) return CFrame.fromMatrix(a.Position+b,a.x,a.y,a.z) end
function CFrame.Angles(x,y,z)
    local sx,cx,sy,cy,sz,cz=math.sin(x),math.cos(x),math.sin(y),math.cos(y),math.sin(z),math.cos(z)
    local rx=CFrame.fromMatrix(Vector3.zero,Vector3.xAxis,Vector3.new(0,cx,sx),Vector3.new(0,-sx,cx))
    local ry=CFrame.fromMatrix(Vector3.zero,Vector3.new(cy,0,-sy),Vector3.yAxis,Vector3.new(sy,0,cy))
    local rz=CFrame.fromMatrix(Vector3.zero,Vector3.new(cz,sz,0),Vector3.new(-sz,cz,0),Vector3.zAxis)
    return rx*ry*rz
end
CFrame.fromOrientation=function(x,y,z) return CFrame.Angles(0,y,0)*CFrame.Angles(x,0,0)*CFrame.Angles(0,0,z) end
function typeof(v) return type(v)=="table" and v._type or type(v) end
Enum={PartType={Ball="Ball",Cylinder="Cylinder"},CollisionFidelity={Default="Default"},RenderFidelity={Automatic="Automatic"}}
fixture={pool={},csg={},failCSG=false}
local I={}; I.__index=I
Instance={new=function(class)
    if class=="INVALID" then error("Invalid class") end
    local p=setmetatable({ClassName=class,Name=class,CFrame=CFrame.new(),Size=Vector3.new(4,1,2),Anchored=false,Transparency=0,attributes={}},I)
    table.insert(fixture.pool,p);return p
end}
function I:IsA(class) return self.ClassName==class or class=="BasePart" and self.ClassName~="Model" and self.ClassName~="Folder" end
function I:SetAttribute(k,v) self.attributes[k]=v end
function I:GetPivot() return self.WorldPivot or self.CFrame end
function I:PivotTo(v) self.WorldPivot=v end
function I:Destroy()
    if self.destroyed then return end
    self.destroyed=true
    for _,p in ipairs(fixture.pool) do if p.Parent==self then p:Destroy() end end
end
function I:SubtractAsync(cutters)
    table.insert(fixture.csg,{kind="subtract",base=self,cutters=cutters})
    if fixture.failCSG then error("Synthetic CSG refusal") end
    local result=Instance.new("UnionOperation");result.CFrame=self.CFrame;return result
end
function I:UnionAsync(parts)
    table.insert(fixture.csg,{kind="union",base=self,parts=parts})
    if fixture.failCSG then error("Synthetic CSG refusal") end
    local result=Instance.new("UnionOperation");result.CFrame=self.CFrame;return result
end
fixture.workspace=Instance.new("Folder")
function resolveRef(ref) return fixture.refs and fixture.refs[ref] or ref=="game.Workspace" and fixture.workspace or nil,"not found" end
function describeRef(inst) return {id=inst.Name,name=inst.Name,className=inst.ClassName,instance=inst} end
function waypoint() end
function waitMeasurable() return {mock=true} end
function ok(result) return {ok=true,result=result} end
function failCode(code,message,details) return {ok=false,code=code,error=message,details=details} end
MASTER_BUILD={};tools={}
